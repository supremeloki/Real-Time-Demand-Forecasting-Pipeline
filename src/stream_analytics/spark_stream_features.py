import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, "src"))

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    from_json,
    col,
    window,
    to_timestamp,
    current_timestamp,
)
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType,
    IntegerType,
)
from src.utils.config_reader import ConfigReader
from src.utils.logging_setup import setup_logging

logger = setup_logging(__name__)


class SparkStreamFeatures:
    def __init__(self, env: str = "dev"):
        self.config = ConfigReader(env)
        self.spark = self._init_spark_session()
        self.kafka_bootstrap_servers = self.config.get("kafka.bootstrap_servers")
        self.kafka_input_topic = self.config.get("kafka.input_topic")
        self.kafka_output_topic = self.config.get("kafka.output_topic")
        self.grid_size_km = self.config.get(
            "features_params.feature_engineering.grid_size_km"
        )
        self.lookback_windows_min = self.config.get(
            "features_params.feature_engineering.lookback_windows_min"
        )

    def _init_spark_session(self):
        spark_master = self.config.get("spark.master")
        app_name = self.config.get("spark.app_name")
        spark_configs = self.config.get("spark.configs", {})

        builder = SparkSession.builder.appName(app_name).master(spark_master)
        for k, v in spark_configs.items():
            builder = builder.config(k, v)

        builder = builder.config(
            "spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1"
        )
        return builder.getOrCreate()

    def _get_demand_event_schema(self):
        return StructType(
            [
                StructField("event_timestamp", StringType()),
                StructField("pickup_latitude", DoubleType()),
                StructField("pickup_longitude", DoubleType()),
                StructField("hour_of_day", IntegerType()),
                StructField("day_of_week", IntegerType()),
                StructField("is_weekend", IntegerType()),
                StructField("is_holiday", IntegerType()),
                StructField("peak_hour_indicator", IntegerType()),
                StructField("demand_at_pickup", IntegerType()),
            ]
        )

    def calculate_grid_id(self, latitude, longitude):
        grid_lat = (latitude // (self.grid_size_km / 111.0)) * (
            self.grid_size_km / 111.0
        )  # Approx 111km per degree lat
        grid_lon = (longitude // (self.grid_size_km / (111.0 * col("cos_lat")))) * (
            self.grid_size_km / (111.0 * col("cos_lat"))
        )
        return grid_lat, grid_lon

    def process_stream(self):
        schema = self._get_demand_event_schema()

        kafka_stream_df = (
            self.spark.readStream.format("kafka")
            .option("kafka.bootstrap.servers", self.kafka_bootstrap_servers)
            .option("subscribe", self.kafka_input_topic)
            .load()
        )

        parsed_stream_df = (
            kafka_stream_df.selectExpr("CAST(value AS STRING) as json_value")
            .withColumn("data", from_json(col("json_value"), schema))
            .select("data.*")
            .withColumn("timestamp", to_timestamp(col("event_timestamp")))
        )

        # Calculate grid IDs
        parsed_stream_df = parsed_stream_df.withColumn(
            "cos_lat", (col("pickup_latitude") * (3.14159 / 180.0)).cos()
        )
        parsed_stream_df = parsed_stream_df.withColumn(
            "grid_id_latitude",
            (col("pickup_latitude") / (self.grid_size_km / 111.0)).cast("int"),
        )
        parsed_stream_df = parsed_stream_df.withColumn(
            "grid_id_longitude",
            (
                col("pickup_longitude") / (self.grid_size_km / (111.0 * col("cos_lat")))
            ).cast("int"),
        )

        # Aggregate demand per grid and time window
        demand_features_df = (
            parsed_stream_df.withWatermark("timestamp", "10 minutes")
            .groupBy(
                window(col("timestamp"), "5 minutes", "5 minutes"),
                col("grid_id_latitude"),
                col("grid_id_longitude"),
                col("hour_of_day"),
                col("day_of_week"),
                col("is_weekend"),
                col("is_holiday"),
                col("peak_hour_indicator"),
            )
            .agg(
                col("demand_at_pickup").alias("raw_demand_count"),
                col("demand_at_pickup").cast("double").alias("demand_sum"),
                col("demand_at_pickup").cast("double").avg().alias("demand_avg"),
            )
        )

        # Add lookback features (simplified for stream, would use stateful operations for production)
        demand_features_df = demand_features_df.withColumn(
            "current_time", current_timestamp()
        )
        for window_size in self.lookback_windows_min:
            demand_features_df = demand_features_df.withColumn(
                f"demand_last_{window_size}min",
                (
                    demand_features_df["demand_sum"] * (60 / window_size)
                ),  # Placeholder, actual logic would be complex stateful aggregation
            )

        # Rename columns to match expected feature names
        demand_features_df = demand_features_df.withColumnRenamed(
            "demand_sum", "demand_last_15min"
        )
        demand_features_df = demand_features_df.withColumnRenamed(
            "demand_last_30min", "demand_last_30min"
        )
        demand_features_df = demand_features_df.withColumnRenamed(
            "demand_last_60min", "demand_last_60min"
        )
        demand_features_df = demand_features_df.withColumnRenamed(
            "demand_last_1440min", "demand_last_1440min"
        )

        output_df = (
            demand_features_df.select(
                col("window.start").alias("feature_window_start"),
                col("window.end").alias("feature_window_end"),
                col("grid_id_latitude"),
                col("grid_id_longitude"),
                col("hour_of_day"),
                col("day_of_week"),
                col("is_weekend"),
                col("is_holiday"),
                col("peak_hour_indicator"),
                col("demand_sum").alias("demand_current_5min"),
                col("demand_last_15min"),
                col("demand_last_30min"),
                col("demand_last_hour"),
                col(
                    "demand_last_1440min"
                ),  # Corresponds to 'demand_same_hour_last_day'
            )
            .withColumn("value", col("struct(*)"))
            .drop("struct(*)")
        )

        query = (
            output_df.selectExpr(
                "CAST(grid_id_latitude AS STRING) as key", "to_json(struct(*)) AS value"
            )
            .writeStream.format("kafka")
            .option("kafka.bootstrap.servers", self.kafka_bootstrap_servers)
            .option("topic", self.kafka_output_topic)
            .option("checkpointLocation", "/tmp/spark-checkpoint")
            .trigger(processingTime="1 minute")
            .outputMode("update")
            .start()
        )

        logger.info(
            f"Spark Structured Streaming started for topic {self.kafka_input_topic}. Writing to {self.kafka_output_topic}"
        )
        query.awaitTermination()


if __name__ == "__main__":
    stream_processor = SparkStreamFeatures(env="dev")
    stream_processor.process_stream()
