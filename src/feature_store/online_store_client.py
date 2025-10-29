import pandas as pd
from datetime import datetime, timedelta
import random


class OnlineFeatureStoreClient:
    def __init__(
        self,
        feature_source_path="data_artifacts/sample_data/batch_processed_features.csv",
    ):
        # For demo, load a small historical set; in prod, connect to actual low-latency store
        try:
            self.historical_features = pd.read_csv(feature_source_path)
            if "event_timestamp" in self.historical_features.columns:
                self.historical_features["timestamp"] = pd.to_datetime(
                    self.historical_features["event_timestamp"]
                )
            elif "timestamp" not in self.historical_features.columns:
                # If no timestamp column, create a mock one
                self.historical_features["timestamp"] = pd.date_range(
                    start=datetime.now() - timedelta(days=1),
                    periods=len(self.historical_features),
                    freq="15min",
                )
            self.historical_features["timestamp"] = pd.to_datetime(
                self.historical_features["timestamp"]
            )
            self.historical_features = self.historical_features.set_index(
                "timestamp"
            ).sort_index()
        except FileNotFoundError:
            # Create empty dataframe if file doesn't exist
            self.historical_features = pd.DataFrame()
            self.historical_features["timestamp"] = pd.DatetimeIndex([])
            self.historical_features = self.historical_features.set_index("timestamp")

    def get_latest_features(self, geohash_id: str, current_time: datetime) -> dict:
        # Simulate fetching real-time features for a given geohash and time
        # In a real system, this would query a Redis/DynamoDB or similar.

        # Mock some recent features if exact match not found
        mock_features = {
            "hour_of_day": current_time.hour,
            "day_of_week": current_time.weekday(),
            "is_weekend": 1 if current_time.weekday() >= 5 else 0,
            "is_holiday": 0,  # Placeholder, would come from external source
            "peak_hour_indicator": (
                1 if 7 <= current_time.hour < 10 or 16 <= current_time.hour < 19 else 0
            ),
            "demand_last_15min": round(random.uniform(20, 80), 2),
            "demand_last_30min": round(random.uniform(40, 150), 2),
            "demand_last_60min": round(random.uniform(100, 300), 2),
            "demand_last_1440min": round(random.uniform(120, 350), 2),
        }

        # For simplicity, just return the mock features.
        # A more complex mock could try to find a closest historical point for a geohash.
        return mock_features


if __name__ == "__main__":
    client = OnlineFeatureStoreClient()
    current_time = datetime.now()
    geohash = "dr5ru"  # Example geohash
    features = client.get_latest_features(geohash, current_time)
    print(f"Features for {geohash} at {current_time.strftime('%Y-%m-%d %H:%M:%S')}:")
    for k, v in features.items():
        print(f"  {k}: {v}")
