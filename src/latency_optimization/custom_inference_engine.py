import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, "src"))

import xgboost as xgb
import pandas as pd
from typing import Union
from src.utils.logging_setup import setup_logging

logger = setup_logging(__name__)


class InferenceEngine:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.optimized_model = None

    def load_optimized_model(self):
        if not os.path.exists(self.model_path):
            logger.error(f"Model artifact not found at {self.model_path}")
            raise FileNotFoundError(f"Model artifact not found at {self.model_path}")

        try:
            self.optimized_model = xgb.Booster()
            self.optimized_model.load_model(self.model_path)
            logger.info(f"XGBoost model loaded from {self.model_path}")
        except xgb.core.XGBoostError as e:
            logger.error(f"Error loading XGBoost model from {self.model_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading model: {e}")
            raise

    def predict(self, input_features: pd.DataFrame) -> pd.Series:
        if self.optimized_model is None:
            raise RuntimeError("Model not loaded. Call load_optimized_model() first.")

        try:
            dmatrix = xgb.DMatrix(input_features)
            predictions = self.optimized_model.predict(dmatrix)
            return pd.Series(predictions, index=input_features.index)
        except Exception as e:
            logger.error(f"Error during inference: {e}")
            raise
