import logging
from typing import Dict, Any, List
import random
import os

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class RegionalModelManager:
    """
    Manages and serves different models optimized for specific geographic regions (geohash prefixes).
    Uses a default model if a region-specific one is not available.
    """

    def __init__(
        self,
        model_registry_client,  # A client to load models (e.g., MLflow, custom registry)
        region_model_map: Dict[str, str],  # Maps geohash prefix to model_name/version
        default_model_name: str = "demand_forecaster_global",
    ):

        self.model_registry_client = model_registry_client
        self.region_model_map = region_model_map
        self.default_model_name = default_model_name
        self.loaded_models: Dict[str, Any] = {}  # Cache for loaded models

        self._load_initial_models()
        logging.info("RegionalModelManager initialized.")

    def _load_initial_models(self):
        """
        Loads the default model and any explicitly mapped regional models at startup.
        """
        # Load default model
        logging.info(f"Loading default model: {self.default_model_name}")
        self.loaded_models[self.default_model_name] = self._get_model_from_registry(
            self.default_model_name
        )

        # Load regional models
        for region_prefix, model_name in self.region_model_map.items():
            if (
                model_name not in self.loaded_models
            ):  # Avoid re-loading if same as default or already loaded
                logging.info(
                    f"Loading regional model for {region_prefix}: {model_name}"
                )
                self.loaded_models[model_name] = self._get_model_from_registry(
                    model_name
                )

        logging.info(f"Successfully loaded {len(self.loaded_models)} unique models.")

    def _get_model_from_registry(self, model_name: str) -> Any:
        """
        Simulates fetching a model from a model registry.
        In a real scenario, this would use MLflowClient, custom API, etc.
        """
        # Placeholder for actual model loading logic
        try:
            # Example: mlflow.pyfunc.load_model(f"models:/{model_name}/Production")
            # For this mock, we return a simple callable that simulates a model
            class MockModel:
                def __init__(self, name):
                    self.name = name

                def predict(self, features: Dict[str, Any]) -> float:
                    # Simple prediction logic for mock
                    return features.get("demand_current_5min", 10.0) * random.uniform(
                        3, 5
                    ) + (5 if "local" in self.name else 0)

            logging.info(f"Mock-loaded model: {model_name}")
            return MockModel(model_name)
        except Exception as e:
            logging.error(
                f"Failed to load model '{model_name}' from registry: {e}. Returning None."
            )
            return None

    def get_model_for_geohash(self, geohash_id: str) -> Any:
        """
        Determines and returns the appropriate model for a given geohash.
        """
        for region_prefix, model_name in self.region_model_map.items():
            if geohash_id.startswith(region_prefix):
                model = self.loaded_models.get(model_name)
                if model:
                    logging.debug(
                        f"Using regional model '{model_name}' for geohash '{geohash_id}'."
                    )
                    return model
                else:
                    logging.warning(
                        f"Regional model '{model_name}' for '{geohash_id}' not found/loaded. Falling back to default."
                    )

        # Fallback to default model
        default_model = self.loaded_models.get(self.default_model_name)
        if not default_model:
            logging.critical("Default model not loaded. Cannot provide any model.")
            raise RuntimeError("No models available.")
        logging.debug(
            f"Using default model '{self.default_model_name}' for geohash '{geohash_id}'."
        )
        return default_model

    def predict(self, geohash_id: str, features: Dict[str, Any]) -> float:
        """
        Gets the appropriate model and makes a prediction.
        """
        model = self.get_model_for_geohash(geohash_id)
        if model:
            return model.predict(features)
        return 0.0  # Fallback for no model


if __name__ == "__main__":
    # Mock Model Registry Client (does nothing for this demo, models are mocked directly)
    class MockModelRegistryClient:
        pass

    # Define regional model mappings (e.g., dr5ru* is a region in Tehran)
    regional_config = {
        "dr5ru": "demand_forecaster_tehran_north",
        "dr5ry": "demand_forecaster_tehran_south_local",
    }

    manager = RegionalModelManager(
        model_registry_client=MockModelRegistryClient(),
        region_model_map=regional_config,
        default_model_name="demand_forecaster_global",
    )

    sample_features = {"hour_of_day": 8, "demand_current_5min": 20.0, "is_weekend": 0}

    print("--- Simulating Regional Model Predictions ---")

    geohash_1 = "dr5ru7z"  # Matches 'dr5ru' prefix
    prediction_1 = manager.predict(geohash_1, sample_features)
    print(f"Prediction for {geohash_1} (Tehran North): {prediction_1:.2f}")

    geohash_2 = "dr5rgaf"  # Does not match any regional prefix, uses default
    prediction_2 = manager.predict(geohash_2, sample_features)
    print(f"Prediction for {geohash_2} (Global Default): {prediction_2:.2f}")

    geohash_3 = "dr5ryab"  # Matches 'dr5ry' prefix
    prediction_3 = manager.predict(geohash_3, sample_features)
    print(f"Prediction for {geohash_3} (Tehran South Local): {prediction_3:.2f}")
