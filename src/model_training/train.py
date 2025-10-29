import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, "src"))

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import mlflow
import mlflow.xgboost
import json
from src.utils.config_reader import ConfigReader
from src.utils.logging_setup import setup_logging
from src.batch_processing.batch_feature_creation import BatchFeatureCreator
from src.model_training.algorithms.xgboost_model import XGBoostModel

logger = setup_logging(__name__)


class ModelTrainer:
    def __init__(self, env: str = "dev"):
        self.config = ConfigReader(env)
        self.mlflow_tracking_uri = self.config.get("model_registry.uri")
        self.model_name = self.config.get("model_registry.model_name")
        self.target_variable = self.config.get("features_params.target_variable")
        self.feature_columns = self._get_feature_columns()

        mlflow.set_tracking_uri(self.mlflow_tracking_uri)
        mlflow.set_experiment(f"{self.model_name}_experiment")

    def _get_feature_columns(self):
        time_feats = self.config.get("features_params.time_features", [])
        location_feats = self.config.get("features_params.location_features", [])
        weather_feats = self.config.get("features_params.weather_features", [])
        demand_hist_feats = self.config.get(
            "features_params.demand_history_features", []
        )

        # Exclude 'grid_id_latitude' and 'grid_id_longitude' if they are not meant as direct features
        # Assuming they are needed for grouping but not direct model input
        # Adjust based on final feature engineering

        all_features = list(
            set(time_feats + location_feats + weather_feats + demand_hist_feats)
        )

        # Manually ensure some are always included and others are removed if they are only for aggregation
        if "grid_id_latitude" in all_features:
            all_features.remove("grid_id_latitude")
        if "grid_id_longitude" in all_features:
            all_features.remove("grid_id_longitude")

        # Current set of generated features in batch_feature_creation.py
        generated_features = [
            "hour_of_day",
            "day_of_week",
            "is_weekend",
            "is_holiday",
            "peak_hour_indicator",
            "demand_last_15min",
            "demand_last_30min",
            "demand_last_60min",
            "demand_last_1440min",  # Represents 'demand_same_hour_last_day'
        ]

        return [
            f for f in generated_features if f != self.target_variable
        ]  # Remove target if present

    def train_model(self):
        logger.info("Starting model training process.")
        feature_creator = BatchFeatureCreator(self.config.env)
        df_features = feature_creator.generate_batch_features()

        X = df_features[self.feature_columns]
        y = df_features[self.target_variable]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=False
        )

        with mlflow.start_run(run_name="Demand_Forecaster_XGBoost") as run:
            xgb_params = {
                "objective": "reg:squarederror",
                "eval_metric": "rmse",
                "n_estimators": 500,
                "learning_rate": 0.05,
                "max_depth": 6,
                "subsample": 0.7,
                "colsample_bytree": 0.7,
                "seed": 42,
                "num_boost_round": 500,  # Added for consistency with XGBoostModel
            }
            mlflow.log_params(xgb_params)

            model_wrapper = XGBoostModel(xgb_params)
            model_wrapper.train(X_train, y_train)

            y_pred = model_wrapper.predict(X_test)

            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)

            mlflow.log_metrics({"rmse": rmse, "mae": mae, "r2": r2})
            logger.info(
                f"Model Metrics - RMSE: {rmse:.4f}, MAE: {mae:.4f}, R2: {r2:.4f}"
            )

            # Log model with MLflow
            mlflow.xgboost.log_model(
                xgb_model=model_wrapper.model,
                artifact_path="demand_forecaster_model",
                registered_model_name=self.model_name,
            )

            # Save feature importance
            feature_importance = model_wrapper.get_feature_importance()
            importance_path = "feature_importance.json"
            with open(importance_path, "w") as f:
                json.dump(feature_importance, f, indent=4)
            mlflow.log_artifact(importance_path)
            os.remove(importance_path)  # Clean up

            logger.info(
                f"Model trained and logged to MLflow as {self.model_name}, version {mlflow.active_run().info.run_id}"
            )


if __name__ == "__main__":
    trainer = ModelTrainer(env="dev")
    trainer.train_model()
