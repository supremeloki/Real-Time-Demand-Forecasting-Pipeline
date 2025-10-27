import logging
from typing import Dict, Any, List
from datetime import datetime
import random
import numpy as np
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MetricAnomalyHub:
    """
    Centralizes the detection and alerting for anomalies across various operational and ML metrics.
    Connects to different anomaly detectors and provides a unified view.
    """
    def __init__(self, alert_threshold: float = 0.8):
        self.alert_threshold = alert_threshold
        self.registered_detectors: Dict[str, Any] = {} # e.g., {'data_drift': ConceptDriftDetector_instance}
        self.anomaly_history: List[Dict[str, Any]] = []
        logging.info("MetricAnomalyHub initialized.")

    def register_detector(self, detector_name: str, detector_instance: Any):
        """Registers an anomaly detector with the hub."""
        self.registered_detectors[detector_name] = detector_instance
        logging.info(f"Anomaly detector '{detector_name}' registered.")

    def ingest_metrics_and_check_anomalies(self, metric_stream: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Ingests a batch of real-time metrics and checks all registered detectors for anomalies.
        Returns a list of detected anomalies.
        """
        detected_anomalies = []
        current_time = datetime.now().isoformat()

        for detector_name, detector in self.registered_detectors.items():
            try:
                # This part is highly detector-specific. For demo, we simulate
                # the detector processing the metrics and returning a status.
                is_anomaly = False
                anomaly_details = {}

                if detector_name == "demand_forecast_drift":
                    # Assume detector.ingest_data_point(metric_stream['predicted_demand'])
                    # and detector.detect_drift() would be called.
                    # For mock:
                    if random.random() < 0.03: # 3% chance of demand drift anomaly
                        is_anomaly = True
                        anomaly_details = {"feature": "predicted_demand", "severity": random.uniform(0.7, 0.95)}
                
                elif detector_name == "resource_cpu_spike":
                    cpu_util = metric_stream.get('cpu_utilization')
                    if cpu_util is not None and cpu_util > 0.9: # Simple rule-based spike
                        is_anomaly = True
                        anomaly_details = {"metric": "cpu_utilization", "value": cpu_util, "severity": cpu_util}

                elif detector_name == "model_prediction_variance":
                    # Assume detector.score_ensemble_confidence(individual_preds)['confidence_level'] == 'LOW'
                    # For mock:
                    if random.random() < 0.05: # 5% chance of high prediction variance
                        is_anomaly = True
                        anomaly_details = {"metric": "prediction_confidence", "severity": random.uniform(0.6, 0.8)}

                if is_anomaly:
                    anomaly_record = {
                        "timestamp": current_time,
                        "detector": detector_name,
                        "details": anomaly_details,
                        "alert_raised": anomaly_details.get("severity", 0) >= self.alert_threshold
                    }
                    detected_anomalies.append(anomaly_record)
                    self.anomaly_history.append(anomaly_record)
                    logging.error(f"ANOMALY DETECTED by '{detector_name}': {anomaly_record}")
            except Exception as e:
                logging.error(f"Error running detector '{detector_name}': {e}")
        
        return detected_anomalies

if __name__ == '__main__':
    hub = MetricAnomalyHub(alert_threshold=0.8)

    # Mock detectors (replace with actual instances from src/monitoring/*)
    class MockDriftDetector:
        def detect_drift(self, data): return False
    class MockResourceDetector:
        def check_spike(self, cpu_util): return False
    class MockModelConfidenceDetector:
        def score_confidence(self, preds): return {"confidence_level": "HIGH", "confidence_score": 0.9}

    hub.register_detector("demand_forecast_drift", MockDriftDetector())
    hub.register_detector("resource_cpu_spike", MockResourceDetector())
    hub.register_detector("model_prediction_variance", MockModelConfidenceDetector())

    print("--- Simulating Metric Stream and Anomaly Detection ---")
    for i in range(20):
        print(f"\n--- Cycle {i+1} ---")
        mock_metrics = {
            "predicted_demand": random.uniform(50, 200),
            "cpu_utilization": random.uniform(0.4, 0.8),
            "qps": random.uniform(200, 1000)
        }
        
        # Manually inject a CPU spike for demonstration
        if i == 5:
            mock_metrics["cpu_utilization"] = 0.95
            mock_metrics["predicted_demand"] = 300 # Also a high demand
        if i == 12:
            mock_metrics["cpu_utilization"] = 0.2
            mock_metrics["predicted_demand"] = 20
            
        anomalies = hub.ingest_metrics_and_check_anomalies(mock_metrics)
        if anomalies:
            for anomaly in anomalies:
                print(f"  Anomaly: {anomaly['detector']}, Alert: {anomaly['alert_raised']}, Details: {anomaly['details']}")
        else:
            print("  No anomalies detected.")
        time.sleep(0.5)