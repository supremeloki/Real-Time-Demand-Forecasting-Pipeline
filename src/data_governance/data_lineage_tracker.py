import logging
from typing import Dict, Any, List
from datetime import datetime
import json

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class DataLineageTracker:
    """
    Tracks the lineage (origin, transformations, destinations) of data assets within the ML pipeline.
    This helps in debugging, compliance, and understanding data flow impact.
    """

    def __init__(
        self, lineage_storage_path: str = "/var/log/snapp_ml/data_lineage.log"
    ):
        self.lineage_storage_path = lineage_storage_path
        logging.info(
            f"DataLineageTracker initialized. Lineage logs to {lineage_storage_path}"
        )

    def _log_lineage_event(self, event: Dict[str, Any]):
        """Writes a lineage event to a persistent log."""
        try:
            with open(self.lineage_storage_path, "a") as f:
                f.write(json.dumps(event) + "\n")
            logging.debug(f"Lineage event logged: {event}")
        except IOError as e:
            logging.error(
                f"Failed to write lineage log to {self.lineage_storage_path}: {e}"
            )

    def track_transformation(
        self,
        source_asset_id: str,
        target_asset_id: str,
        transformation_name: str,
        process_id: str,
        input_schema_version: str = None,
        output_schema_version: str = None,
        params: Dict[str, Any] = None,
    ):
        """
        Records a data transformation event.
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "transformation",
            "source_asset_id": source_asset_id,
            "target_asset_id": target_asset_id,
            "transformation_name": transformation_name,
            "process_id": process_id,
            "input_schema_version": input_schema_version,
            "output_schema_version": output_schema_version,
            "parameters": params or {},
        }
        self._log_lineage_event(event)

    def track_data_creation(
        self,
        asset_id: str,
        source_system: str,
        creation_process_id: str,
        schema_version: str = None,
        details: Dict[str, Any] = None,
    ):
        """
        Records the creation of a new data asset.
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "creation",
            "asset_id": asset_id,
            "source_system": source_system,
            "creation_process_id": creation_process_id,
            "schema_version": schema_version,
            "details": details or {},
        }
        self._log_lineage_event(event)

    def track_data_consumption(
        self,
        consumer_id: str,  # e.g., 'model_training_job_vX', 'inference_api_Y'
        consumed_asset_id: str,
        consumption_process_id: str,
        schema_version: str = None,
        details: Dict[str, Any] = None,
    ):
        """
        Records the consumption of a data asset by another process/service.
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "consumption",
            "consumer_id": consumer_id,
            "consumed_asset_id": consumed_asset_id,
            "consumption_process_id": consumption_process_id,
            "schema_version": schema_version,
            "details": details or {},
        }
        self._log_lineage_event(event)


if __name__ == "__main__":
    tracker = DataLineageTracker(lineage_storage_path="/tmp/snapp_ml_lineage.log")

    # Ensure the log file is clean for a fresh run
    with open("/tmp/snapp_ml_lineage.log", "w") as f:
        pass

    print("--- Simulating Data Lineage Tracking ---")

    # Simulate raw data generation
    tracker.track_data_creation(
        asset_id="raw_ride_events_kafka_topic",
        source_system="KafkaProducer",
        creation_process_id="event_simulator_v1.0",
        schema_version="v1.0",
        details={"topic": "snapp.ride_events_raw"},
    )

    # Simulate batch feature creation
    tracker.track_transformation(
        source_asset_id="raw_ride_events_kafka_topic",
        target_asset_id="batch_features_s3",
        transformation_name="batch_feature_engineering",
        process_id="spark_batch_job_v1.2",
        input_schema_version="v1.0",
        output_schema_version="v2.0",
        params={"window_size": "15min", "aggregations": ["sum", "avg"]},
    )

    # Simulate model training consuming batch features
    tracker.track_data_consumption(
        consumer_id="model_training_job_v2.1",
        consumed_asset_id="batch_features_s3",
        consumption_process_id="train_xgboost_v2.1",
        schema_version="v2.0",
        details={"model_name": "DemandForecaster", "run_id": "mlflow_run_xyz"},
    )

    # Simulate real-time features being generated and consumed by inference API
    tracker.track_transformation(
        source_asset_id="raw_ride_events_kafka_topic",  # Stream from Kafka
        target_asset_id="online_features_redis",
        transformation_name="realtime_feature_engineering",
        process_id="spark_streaming_job_v1.5",
        input_schema_version="v1.0",
        output_schema_version="v2.1",
        params={"streaming_interval": "5s"},
    )

    tracker.track_data_consumption(
        consumer_id="inference_api_instance_X",
        consumed_asset_id="online_features_redis",
        consumption_process_id="model_inference_v2.1",
        schema_version="v2.1",
        details={"model_version": "DemandForecaster/Production"},
    )

    print(f"\nData lineage log saved to: {tracker.lineage_storage_path}")
    # You can check the content of /tmp/snapp_ml_lineage.log
