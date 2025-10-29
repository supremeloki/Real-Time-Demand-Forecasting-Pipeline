import pandas as pd
from datetime import datetime, timedelta
import logging
import random

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class FeatureStoreBackfillManager:
    def __init__(
        self,
        target_store_client,
        historical_data_path="data_artifacts/sample_data/synthetic_snapp_data.csv",
    ):
        self.target_store_client = target_store_client  # This would be an actual Feature Store client (e.g., Feast, Redis)
        self.historical_data_path = historical_data_path
        logging.info("FeatureStoreBackfillManager initialized.")

    def _load_raw_historical_data(
        self, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        # In a real scenario, load from data lake (S3, GCS) or data warehouse (Snowflake, BigQuery)
        logging.info(
            f"Loading raw historical data from {self.historical_data_path} for {start_date} to {end_date}"
        )
        try:
            df = pd.read_csv(self.historical_data_path)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df_filtered = df[
                (df["timestamp"] >= start_date) & (df["timestamp"] < end_date)
            ].copy()
            logging.info(f"Loaded {len(df_filtered)} raw events.")
            return df_filtered
        except FileNotFoundError:
            logging.error(
                f"Historical data file not found at {self.historical_data_path}"
            )
            return pd.DataFrame()
        except Exception as e:
            logging.error(f"Error loading historical data: {e}")
            return pd.DataFrame()

    def _generate_features_from_raw(self, raw_events: pd.DataFrame) -> pd.DataFrame:
        # This simulates the batch_feature_creation.py logic for a specific time window
        # In practice, this would call a dedicated batch feature transformation service
        if raw_events.empty:
            return pd.DataFrame()

        logging.info(f"Generating features for {len(raw_events)} raw events.")
        # Simplified feature generation for demo:
        raw_events["hour_of_day"] = raw_events["timestamp"].dt.hour
        raw_events["day_of_week"] = raw_events["timestamp"].dt.dayofweek
        raw_events["is_weekend"] = (raw_events["timestamp"].dt.dayofweek >= 5).astype(
            int
        )

        # Aggregate demand features (highly simplified)
        # For a true backfill, you'd apply the same logic as batch_feature_creation.py
        # This mock simply calculates demand per geohash and time slice
        features_list = []
        for (geohash, time_window), group in raw_events.groupby(
            ["geohash_id", pd.Grouper(key="timestamp", freq="5min")]
        ):
            features = {
                "timestamp": time_window,
                "geohash_id": geohash,
                "hour_of_day": time_window.hour,
                "day_of_week": time_window.weekday(),
                "is_weekend": 1 if time_window.weekday() >= 5 else 0,
                "peak_hour_indicator": (
                    1
                    if 7 <= time_window.hour < 10 or 16 <= time_window.hour < 19
                    else 0
                ),
                "demand_current_5min": group["request_count"].sum(),
                "demand_last_15min": group["request_count"].sum()
                * random.uniform(2.5, 3.5),  # Mock historical aggregates
                "demand_last_30min": group["request_count"].sum()
                * random.uniform(5.5, 6.5),
                "demand_last_hour": group["request_count"].sum()
                * random.uniform(10.5, 12.5),
                "demand_last_1440min": group["request_count"].sum()
                * random.uniform(100, 150),
            }
            features_list.append(features)

        return pd.DataFrame(features_list)

    def backfill_features(self, start_date: datetime, end_date: datetime):
        logging.info(f"Starting feature backfill from {start_date} to {end_date}")

        raw_data = self._load_raw_historical_data(start_date, end_date)
        if raw_data.empty:
            logging.warning("No raw data found for the specified period to backfill.")
            return

        features_df = self._generate_features_from_raw(raw_data)
        if features_df.empty:
            logging.warning(
                "No features generated for the specified period to backfill."
            )
            return

        # Ingest into the target online feature store
        logging.info(
            f"Ingesting {len(features_df)} generated features into the online feature store (simulated)."
        )
        # Example of how a feature store client might work:
        for _, row in features_df.iterrows():
            # self.target_store_client.write_features(row.to_dict()) # Actual write operation
            pass  # Placeholder for actual write

        logging.info(
            f"Successfully completed backfill for {len(features_df)} feature sets."
        )


if __name__ == "__main__":
    # Mock Feature Store Client
    class MockFeatureStoreClient:
        def write_features(self, features: dict):
            logging.info(
                f"Mocking write to FS: {features['geohash_id']} @ {features['timestamp']} with demand {features['demand_current_5min']:.2f}"
            )

    mock_fs_client = MockFeatureStoreClient()
    backfill_manager = FeatureStoreBackfillManager(mock_fs_client)

    # Example backfill for the last 2 days
    end_time = datetime.now()
    start_time = end_time - timedelta(days=2)

    print("\n--- Starting Feature Store Backfill Simulation ---")
    backfill_manager.backfill_features(start_time, end_time)
    print("--- Backfill Simulation Complete ---")
