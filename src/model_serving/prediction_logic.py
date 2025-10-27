import sys
import os
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, 'src'))

import mlflow
import mlflow.xgboost
import pandas as pd
from typing import Dict, Any, List
from src.utils.config_reader import ConfigReader
from src.utils.logging_setup import setup_logging

class XGBoostInferenceEngine:
    def __init__(self, model):
        self.model = model

    def load_optimized_model(self):
        pass  # Model already loaded

    def predict(self, input_features):
        import xgboost as xgb
        dmatrix = xgb.DMatrix(input_features)
        return self.model.predict(dmatrix)

logger = setup_logging(__name__)

class PredictionLogic:
    def __init__(self, env: str = "dev"):
        self.config = ConfigReader(env)
        self.mlflow_tracking_uri = self.config.get("model_registry.uri")
        self.model_name = self.config.get("model_registry.model_name")
        self.target_variable = self.config.get("features_params.target_variable")
        self.feature_columns = self._get_feature_columns()
        self.inference_engine = self._load_model_with_inference_engine()

    def _get_feature_columns(self):
        # Must match features used during training in src/model_training/train.py
        generated_features = [
            'hour_of_day', 'day_of_week', 'is_weekend', 'is_holiday', 'peak_hour_indicator',
            'demand_last_15min', 'demand_last_30min', 'demand_last_60min',
            'demand_last_1440min'
        ]
        return generated_features

    def _load_model_with_inference_engine(self):
        try:
            mlflow.set_tracking_uri(self.mlflow_tracking_uri)
            model_uri = f"models:/{self.model_name}/Production"

            # Fetch the latest production model version
            client = mlflow.tracking.MlflowClient()
            try:
                latest_version = client.get_latest_versions(self.model_name, stages=["Production"])[0].version
            except IndexError:
                # No production model, get any latest version
                latest_version = client.get_latest_versions(self.model_name)[0].version

            # Load model directly using MLflow pyfunc
            logger.info(f"Loading model '{self.model_name}' version {latest_version}")
            model = mlflow.xgboost.load_model(f"models:/{self.model_name}/{latest_version}")

            # Wrap in a simple inference engine that mimics the interface
            inference_engine = XGBoostInferenceEngine(model)
            logger.info(f"Loaded production model '{self.model_name}' version {latest_version} for inference.")
            return inference_engine
        except Exception as e:
            logger.error(f"Failed to load production model: {e}")
            raise

    def predict_demand(self, features: Dict[str, Any]) -> float:
        input_df = pd.DataFrame([features])[self.feature_columns]
        
        if self.inference_engine:
            prediction = self.inference_engine.predict(input_df)
            return float(prediction[0])
        else:
            logger.error("Inference engine not loaded.")
            return 0.0

    def batch_predict_demand(self, features_list: List[Dict[str, Any]]) -> List[float]:
        input_df = pd.DataFrame(features_list)[self.feature_columns]
        
        if self.inference_engine:
            predictions = self.inference_engine.predict(input_df)
            return predictions.tolist()
        else:
            logger.error("Inference engine not loaded.")
            return [0.0] * len(features_list)
