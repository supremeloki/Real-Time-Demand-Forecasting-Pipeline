import pandas as pd
from scipy.stats import kstest, wasserstein_distance  # type: ignore[import]
import numpy as np
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import sys
import os
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, 'src'))
from src.utils.logging_setup import setup_logging  # noqa
from src.utils.config_reader import ConfigReader  # noqa

logger = setup_logging(__name__)

class DataDriftDetector:
    def __init__(self, env: str = "dev"):
        self.config = ConfigReader(env)
        self.feature_columns = self._get_feature_columns()
        self.drift_thresholds = self.config.get("monitoring.drift_thresholds", {"ks_pvalue": 0.05, "wasserstein_threshold": 0.1})
        self.baseline_data_path = "data_artifacts/sample_data/batch_processed_features.csv" # Or from a feature store

    def _get_feature_columns(self):
        generated_features = [
            'hour_of_day', 'day_of_week', 'is_weekend', 'is_holiday', 'peak_hour_indicator',
            'demand_last_15min', 'demand_last_30min', 'demand_last_60min',
            'demand_last_1440min'
        ]
        return generated_features

    def load_baseline_data(self) -> pd.DataFrame:
        try:
            baseline_df = pd.read_csv(self.baseline_data_path)
            return baseline_df[self.feature_columns]
        except FileNotFoundError:
            logger.error(f"Baseline data not found at {self.baseline_data_path}. Please generate it first.")
            raise

    def detect_drift(self, current_data: pd.DataFrame, baseline_data: pd.DataFrame) -> Dict[str, Any]:
        drift_report: Dict[str, Any] = {"timestamp": datetime.now().isoformat(), "feature_drift": {}}

        for col in self.feature_columns:
            if col not in current_data.columns or col not in baseline_data.columns:
                logger.warning(f"Feature '{col}' missing in current or baseline data. Skipping drift detection.")
                continue

            current_series = current_data[col].dropna()
            baseline_series = baseline_data[col].dropna()

            if current_series.empty or baseline_series.empty:
                logger.warning(f"Feature '{col}' has empty data after dropping NaNs. Skipping drift detection.")
                continue

            # Kolmogorov-Smirnov Test
            try:
                ks_statistic, ks_pvalue = kstest(current_series, baseline_series)
                ks_drift_detected = ks_pvalue < self.drift_thresholds["ks_pvalue"]
            except ValueError as e:
                logger.warning(f"KS test failed for {col}: {e}. Possibly due to identical distributions or insufficient data.")
                ks_statistic, ks_pvalue, ks_drift_detected = np.nan, np.nan, False

            # Wasserstein Distance (Earth Mover's Distance)
            try:
                ws_distance = wasserstein_distance(current_series, baseline_series)
                # Normalizing Wasserstein distance by the range of the feature for comparison
                feature_range = max(baseline_series.max(), current_series.max()) - min(baseline_series.min(), current_series.min())
                normalized_ws_distance = ws_distance / feature_range if feature_range > 0 else 0.0
                ws_drift_detected = normalized_ws_distance > self.drift_thresholds.get("wasserstein_threshold", 0.1)
            except Exception as e:
                logger.warning(f"Wasserstein distance calculation failed for {col}: {e}")
                ws_distance, normalized_ws_distance, ws_drift_detected = np.nan, np.nan, False

            feature_drift: Dict[str, Any] = {
                "ks_pvalue": ks_pvalue,
                "ks_drift_detected": bool(ks_drift_detected),
                "wasserstein_distance": ws_distance,
                "normalized_wasserstein_distance": normalized_ws_distance,
                "ws_drift_detected": bool(ws_drift_detected),
                "overall_drift_detected": bool(ks_drift_detected or ws_drift_detected)
            }
            drift_report["feature_drift"][col] = feature_drift
        
        overall_drift_detected = any(fd["overall_drift_detected"] for fd in drift_report["feature_drift"].values())
        drift_report["overall_drift_detected"] = overall_drift_detected
        
        if overall_drift_detected:
            logger.warning("DATA DRIFT DETECTED!")
        else:
            logger.info("No significant data drift detected.")

        return drift_report

    def run_drift_detection_pipeline(self, current_data_source: Optional[str] = None) -> Dict[str, Any]:
        baseline_df = self.load_baseline_data()
        
        # Simulate loading current data (e.g., from a real-time feature store or Kafka stream)
        # For demo, we'll simulate current data by slightly altering baseline or generating new synthetic data
        if current_data_source:
            # In a real scenario, this would load from Kafka, DB, etc.
            current_df = pd.read_csv(current_data_source)[self.feature_columns]
            logger.info(f"Loaded current data from {current_data_source}")
        else:
            logger.info("Generating simulated current data for drift detection (slightly modified baseline).")
            current_df = baseline_df.copy()
            # Introduce some synthetic drift
            if 'demand_last_15min' in current_df.columns:
                current_df['demand_last_15min'] = current_df['demand_last_15min'] * np.random.normal(1.1, 0.1, len(current_df))
            if 'hour_of_day' in current_df.columns:
                current_df['hour_of_day'] = (current_df['hour_of_day'] + np.random.randint(-1, 2, len(current_df))) % 24

        drift_results = self.detect_drift(current_df, baseline_df)
        
        output_path = f"model_experiments/monitoring/drift_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_path, 'w') as f:
            json.dump(drift_results, f, indent=4)
        logger.info(f"Drift detection report saved to {output_path}")
        return drift_results

if __name__ == "__main__":
    from src.batch_processing.batch_feature_creation import BatchFeatureCreator  # noqa

    # Ensure baseline data exists
    feature_creator = BatchFeatureCreator(env="dev")
    features_df = feature_creator.generate_batch_features()
    baseline_output_path = "data_artifacts/sample_data/batch_processed_features.csv"
    features_df.to_csv(baseline_output_path, index=False)
    logger.info(f"Baseline features created for drift detection: {baseline_output_path}")

    # Run drift detection
    drift_detector = DataDriftDetector(env="dev")
    drift_report = drift_detector.run_drift_detection_pipeline()
    print(json.dumps(drift_report, indent=4))