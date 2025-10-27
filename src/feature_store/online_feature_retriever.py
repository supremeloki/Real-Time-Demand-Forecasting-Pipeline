import pandas as pd
from datetime import datetime, timedelta
import random
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class OnlineFeatureRetriever:
    def __init__(self, feature_store_endpoint: str = "http://mock-feast-store:8080"):
        self.feature_store_endpoint = feature_store_endpoint
        logging.info(f"OnlineFeatureRetriever connected to {self.feature_store_endpoint}")

    def get_realtime_features(self, entity_keys: dict) -> dict:
        """
        Simulates fetching real-time features from an online feature store for given entity keys.
        """
        logging.debug(f"Querying online feature store for entities: {entity_keys}")
        
        # In a real scenario, this would involve an HTTP call or SDK interaction
        # For demo, generate synthetic features based on entity keys
        geohash_id = entity_keys.get("geohash_id", "unknown")
        current_time = datetime.now()

        # Simulate feature values that might come from streaming pipelines
        features = {
            "prediction_timestamp": current_time.isoformat(),
            "geohash_id": geohash_id,
            "hourly_peak_factor": round(1.0 + random.uniform(-0.3, 0.7), 2),
            "recent_ride_rate_5min": round(random.uniform(5, 30), 2),
            "avg_wait_time_15min": round(random.uniform(2, 15), 2),
            "weather_temp_c": round(random.uniform(10, 35), 1),
            "event_density_score": round(random.uniform(0, 10), 1),
            "driver_availability_ratio": round(random.uniform(0.5, 1.5), 2)
        }
        logging.debug(f"Retrieved features for {geohash_id}: {features}")
        return features

if __name__ == '__main__':
    retriever = OnlineFeatureRetriever()
    
    # Example entity keys for a prediction request
    entity_id_tehran_north = {"geohash_id": "dr5ru"}
    entity_id_tehran_central = {"geohash_id": "dr5rz"}

    print("--- Simulating Online Feature Retrieval ---")
    features_north = retriever.get_realtime_features(entity_id_tehran_north)
    print(f"\nFeatures for {entity_id_tehran_north['geohash_id']}:")
    for k, v in features_north.items():
        print(f"  {k}: {v}")

    features_central = retriever.get_realtime_features(entity_id_tehran_central)
    print(f"\nFeatures for {entity_id_tehran_central['geohash_id']}:")
    for k, v in features_central.items():
        print(f"  {k}: {v}")