import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import logging
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RealtimeAnomalyDetector:
    def __init__(self, contamination: float = 0.05, window_size: int = 100):
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.window_size = window_size
        self.data_buffer = []
        logging.info(f"Initialized RealtimeAnomalyDetector with contamination={contamination} and window_size={window_size}")

    def ingest_data_point(self, features: dict) -> None:
        # Assuming 'demand_last_15min' is a key feature for anomaly detection
        # In a real system, you'd select multiple relevant features.
        self.data_buffer.append(features.get('demand_last_15min', 0))
        if len(self.data_buffer) > self.window_size:
            self.data_buffer.pop(0)

    def detect_anomaly(self, current_features: dict) -> bool:
        if len(self.data_buffer) < self.window_size:
            logging.info("Buffer not full, skipping anomaly detection for now.")
            return False

        # Create a dataframe for the Isolation Forest model
        df_train = pd.DataFrame(self.data_buffer, columns=['demand_last_15min'])

        try:
            self.model.fit(df_train)
            current_demand = current_features.get('demand_last_15min', 0)
            prediction = self.model.predict(np.array([[current_demand]]))
            
            is_anomaly = prediction == -1 # IsolationForest predicts -1 for anomalies, 1 for inliers
            
            if is_anomaly:
                logging.warning(f"Anomaly detected! Current demand: {current_demand} at {datetime.now()}")
            else:
                logging.debug(f"No anomaly detected. Current demand: {current_demand}")
            return bool(is_anomaly)
        except Exception as e:
            logging.error(f"Error during anomaly detection: {e}")
            return False

if __name__ == '__main__':
    detector = RealtimeAnomalyDetector()

    # Simulate ingesting a stream of features
    print("--- Simulating data stream and anomaly detection ---")
    for i in range(120): # Simulate 120 data points
        mock_features = {
            "demand_last_15min": np.random.normal(loc=20, scale=5)
        }
        if i == 70: # Inject an anomaly
            mock_features["demand_last_15min"] = 100
        if i == 80: # Inject another anomaly
            mock_features["demand_last_15min"] = 0
            
        detector.ingest_data_point(mock_features)
        if i >= 99: # Start detecting after buffer is full
            is_anomaly = detector.detect_anomaly(mock_features)
            # if is_anomaly:
            #     print(f"Time {i}: Anomaly Detected! Value: {mock_features['demand_current_5min']:.2f}")
            # else:
            #     print(f"Time {i}: Normal. Value: {mock_features['demand_current_5min']:.2f}")
        time.sleep(0.01) # Simulate real-time delay