import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from datetime import datetime, timedelta
import json
from typing import Dict, Any, List
import sys
import os
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, 'src'))

from src.utils.logging_setup import setup_logging
from src.utils.config_reader import ConfigReader
from src.model_serving.prediction_logic import PredictionLogic
from src.batch_processing.batch_feature_creation import BatchFeatureCreator
logger = setup_logging(__name__)

class ModelPerformanceMonitor:
    def __init__(self, env: str = "dev"):
        self.config = ConfigReader(env)
        self.prediction_logic = PredictionLogic(env) # Use the same prediction logic for consistency
        self.target_variable = self.config.get("features_params.target_variable")
        self.monitor_interval_minutes = self.config.get("monitoring.performance_interval_minutes", 60)
        self.performance_thresholds = self.config.get("monitoring.performance_thresholds", {"rmse_max": 7.0, "r2_min": 0.7})
        self.historical_predictions_path = "model_experiments/monitoring/historical_predictions.csv"
        
        # Load historical predictions to compare against if available
        self.historical_predictions = self._load_historical_predictions()

    def _load_historical_predictions(self) -> pd.DataFrame:
        if os.path.exists(self.historical_predictions_path):
            try:
                df = pd.read_csv(self.historical_predictions_path, parse_dates=['timestamp'])
                logger.info(f"Loaded {len(df)} historical predictions for monitoring.")
                return df
            except Exception as e:
                logger.warning(f"Could not load historical predictions: {e}. Starting fresh.")
        return pd.DataFrame(columns=['timestamp', 'grid_id_latitude', 'grid_id_longitude', 'actual', 'predicted'])

    def _save_historical_predictions(self):
        self.historical_predictions.to_csv(self.historical_predictions_path, index=False)
        logger.info(f"Saved {len(self.historical_predictions)} historical predictions.")

    def fetch_actual_demand(self, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        logger.info(f"Fetching actual demand for {start_time} to {end_time}")
        # In a real system, this would query a data warehouse/database for actual ride completions
        # For demo, we'll re-run batch feature creation and use the target variable as actuals
        feature_creator = BatchFeatureCreator(self.config.env)
        df_features = feature_creator.generate_batch_features()
        
        df_features['timestamp'] = pd.to_datetime(df_features['feature_window_start'])
        
        actuals_df = df_features[
            (df_features['timestamp'] >= start_time) & (df_features['timestamp'] < end_time)
        ].rename(columns={self.target_variable: 'actual'})
        
        return actuals_df[['timestamp', 'grid_id_latitude', 'grid_id_longitude', 'actual'] + self.prediction_logic.feature_columns]

    def generate_predictions_for_monitoring(self, feature_data: pd.DataFrame) -> pd.DataFrame:
        if feature_data.empty:
            return pd.DataFrame()

        features_for_pred = feature_data[self.prediction_logic.feature_columns].to_dict(orient='records')
        predictions = self.prediction_logic.batch_predict_demand(features_for_pred)
        
        feature_data['predicted'] = predictions
        return feature_data[['timestamp', 'grid_id_latitude', 'grid_id_longitude', 'actual', 'predicted']]

    def evaluate_performance(self, df_metrics: pd.DataFrame) -> Dict[str, Any]:
        if df_metrics.empty:
            return {"status": "no_data", "message": "No data available for performance evaluation."}
        
        rmse = np.sqrt(mean_squared_error(df_metrics['actual'], df_metrics['predicted']))
        mae = mean_absolute_error(df_metrics['actual'], df_metrics['predicted'])
        r2 = r2_score(df_metrics['actual'], df_metrics['predicted'])

        status = "ok"
        alerts = []
        if rmse > self.performance_thresholds["rmse_max"]:
            status = "alert"
            alerts.append(f"RMSE ({rmse:.2f}) exceeded threshold ({self.performance_thresholds['rmse_max']}).")
        if r2 < self.performance_thresholds["r2_min"]:
            status = "alert"
            alerts.append(f"R2 score ({r2:.2f}) fell below threshold ({self.performance_thresholds['r2_min']}).")

        report = {
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "rmse": rmse,
                "mae": mae,
                "r2": r2,
                "num_predictions": len(df_metrics)
            },
            "status": status,
            "alerts": alerts
        }

        if status == "alert":
            logger.error(f"MODEL PERFORMANCE ALERT: {', '.join(alerts)}")
        else:
            logger.info(f"Model performance OK. RMSE: {rmse:.2f}, R2: {r2:.2f}")

        return report

    def run_performance_monitoring_pipeline(self):
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=self.monitor_interval_minutes)

        actual_features_df = self.fetch_actual_demand(start_time, end_time)
        if actual_features_df.empty:
            logger.warning("No new actual data found for monitoring period. Skipping performance check.")
            return {"status": "skipped", "message": "No new actual data."}
        
        predictions_df = self.generate_predictions_for_monitoring(actual_features_df)
        
        # Merge new predictions with historical data
        self.historical_predictions = pd.concat([self.historical_predictions, predictions_df], ignore_index=True)
        self.historical_predictions = self.historical_predictions.drop_duplicates(subset=['timestamp', 'grid_id_latitude', 'grid_id_longitude'], keep='last')
        self.historical_predictions = self.historical_predictions.sort_values('timestamp').reset_index(drop=True)
        
        self._save_historical_predictions()

        report = self.evaluate_performance(predictions_df)
        
        output_path = f"model_experiments/monitoring/performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=4)
        logger.info(f"Performance report saved to {output_path}")
        return report

if __name__ == "__main__":
    monitor = ModelPerformanceMonitor(env="dev")
    monitor.run_performance_monitoring_pipeline()