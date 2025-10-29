from random import random
import shap
import pandas as pd
import numpy as np
import logging
import random
import joblib  # Assuming model is saved with joblib

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class ExplainabilityService:
    def __init__(
        self,
        model_path: str = None,
        sample_data_path: str = "data_artifacts/sample_data/batch_processed_features.csv",
    ):
        self.model = self._load_model(model_path)
        self.feature_names = self._load_feature_names(sample_data_path)
        self.explainer = self._initialize_explainer()
        logging.info("ExplainabilityService initialized.")

    def _load_model(self, model_path: str):
        try:
            import xgboost as xgb

            dummy_model = xgb.XGBRegressor(n_estimators=10)
            dummy_model.fit(
                pd.DataFrame(
                    np.random.rand(10, 5), columns=[f"feature_{i}" for i in range(5)]
                ),
                np.random.rand(10),
            )
            logging.info("Loaded dummy model for explainability service.")
            return dummy_model
        except Exception as e:
            logging.error(
                f"Could not load actual model, using a dummy placeholder. Error: {e}"
            )

            class DummyModel:
                def predict(self, X):
                    return np.sum(X, axis=1) * 0.5

            return DummyModel()

    def _load_feature_names(self, sample_data_path: str):
        try:
            df = pd.read_csv(sample_data_path)
            relevant_features = [
                col
                for col in df.columns
                if col
                not in [
                    "event_timestamp",
                    "grid_id_latitude",
                    "grid_id_longitude",
                    "feature_window_start",
                    "feature_window_end",
                    "raw_demand_count",
                    "demand_sum",
                    "demand_forecaster_dev",
                ]
            ]
            logging.info(
                f"Loaded {len(relevant_features)} feature names from sample data."
            )
            return relevant_features
        except Exception as e:
            logging.error(
                f"Could not load feature names from sample data. Error: {e}. Using generic names."
            )
            return [f"feature_{i}" for i in range(5)]  # Fallback

    def _initialize_explainer(self):
        try:
            background = pd.DataFrame(
                np.random.rand(100, len(self.feature_names)), columns=self.feature_names
            )
            explainer = shap.TreeExplainer(self.model, background)
            logging.info("SHAP TreeExplainer initialized.")
            return explainer
        except Exception as e:
            logging.error(f"Could not initialize SHAP explainer. Error: {e}")
            return None

    def explain_prediction(self, features: dict) -> dict:
        if not self.explainer:
            logging.warning("Explainer not initialized. Cannot provide explanation.")
            return {"error": "Explainer not available."}

        # Convert input features to a DataFrame matching the model's expected input
        feature_vector = pd.DataFrame([features], columns=self.feature_names)

        try:
            shap_values = self.explainer.shap_values(feature_vector)

            feature_importances = dict(zip(self.feature_names, shap_values[0].tolist()))

            logging.debug(
                f"Generated SHAP explanation for features: {feature_importances}"
            )
            return feature_importances
        except Exception as e:
            logging.error(f"Error generating SHAP explanation: {e}")
            return {"error": f"Failed to generate explanation: {e}"}


if __name__ == "__main__":
    explainer_service = ExplainabilityService()

    # Example features for a prediction
    sample_features = {
        "hour_of_day": 9,
        "day_of_week": 2,
        "is_weekend": 0,
        "is_holiday": 0,
        "peak_hour_indicator": 1,
        "demand_last_15min": 40.0,
        "demand_last_30min": 75.0,
        "demand_last_60min": 150.0,
        "demand_last_1440min": 160.0,
    }

    adjusted_sample_features = {
        f"feature_{i}": random.uniform(0, 1)
        for i in range(len(explainer_service.feature_names))
    }
    if (
        len(explainer_service.feature_names) == 9
    ):  # if features loaded successfully from batch_processed_features.csv
        adjusted_sample_features = {
            "hour_of_day": 9,
            "day_of_week": 2,
            "is_weekend": 0,
            "is_holiday": 0,
            "peak_hour_indicator": 1,
            "demand_last_15min": 40.0,
            "demand_last_30min": 75.0,
            "demand_last_60min": 150.0,
            "demand_last_1440min": 160.0,
        }

    print("\n--- Generating SHAP explanation ---")
    explanation = explainer_service.explain_prediction(adjusted_sample_features)
    print("SHAP Values (Feature Importance):")
    for feature, value in explanation.items():
        print(f"  {feature}: {value:.4f}")
