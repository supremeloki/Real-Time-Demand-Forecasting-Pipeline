import logging
from typing import Dict, Any, List
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EnsemblePredictor:
    def __init__(self, model_clients: List[Any], weights: List[float] = None):
        if not model_clients:
            raise ValueError("EnsemblePredictor requires at least one model client.")
        self.model_clients = model_clients
        self.weights = weights if weights else [1.0 / len(model_clients)] * len(model_clients)
        if len(self.weights) != len(self.model_clients):
            raise ValueError("Number of weights must match number of model clients.")
        if not np.isclose(sum(self.weights), 1.0):
            logging.warning("Ensemble weights do not sum to 1.0. They will be normalized.")
            self.weights = [w / sum(self.weights) for w in self.weights]
        
        logging.info(f"EnsemblePredictor initialized with {len(model_clients)} models and weights: {self.weights}")

    def predict(self, features: Dict[str, Any]) -> float:
        """
        Combines predictions from multiple models using a weighted average.
        """
        individual_predictions = []
        for i, client in enumerate(self.model_clients):
            try:
                # Assuming each client has a .predict(features) method
                prediction = client.predict(features)
                individual_predictions.append(prediction)
                logging.debug(f"Model {i+1} predicted: {prediction:.2f}")
            except Exception as e:
                logging.error(f"Error getting prediction from model client {i+1}: {e}. Skipping this model.")
                # Optionally, use a default value or re-normalize weights
                individual_predictions.append(0.0) # Or some other fallback

        if not individual_predictions:
            logging.error("No successful predictions from any model in the ensemble.")
            return 0.0 # Fallback

        # Apply weights to successful predictions
        # Filter out predictions from failed models (if any) and adjust weights
        valid_predictions = [pred for pred in individual_predictions if pred is not None]
        if len(valid_predictions) != len(individual_predictions):
            logging.warning(f"Some models failed. Re-normalizing weights for {len(valid_predictions)} successful models.")
            # Simple re-normalization: just use successful predictions and average
            if not valid_predictions: return 0.0
            ensemble_prediction = np.mean(valid_predictions) # Fallback to simple average
        else:
            ensemble_prediction = np.average(individual_predictions, weights=self.weights)
        
        logging.info(f"Ensemble prediction: {ensemble_prediction:.2f}")
        return float(ensemble_prediction)

if __name__ == '__main__':
    # Mock Model Clients
    class MockModelClient:
        def __init__(self, model_id, bias=0.0):
            self.model_id = model_id
            self.bias = bias
            logging.info(f"MockModelClient {model_id} created.")

        def predict(self, features: Dict[str, Any]) -> float:
            # Simple mock prediction based on a feature and some randomness
            base_prediction = features.get('demand_current_5min', 10.0) * 5
            prediction = base_prediction + self.bias + np.random.uniform(-5, 5)
            # Simulate a rare failure
            if np.random.rand() < 0.05:
                raise RuntimeError(f"MockModelClient {self.model_id} simulated failure.")
            return max(0.0, prediction)

    model_client_1 = MockModelClient("XGBoost", bias=5.0)
    model_client_2 = MockModelClient("LightGBM", bias=-2.0)
    model_client_3 = MockModelClient("NeuralNet", bias=8.0)

    # Test with equal weights
    ensemble_equal_weights = EnsemblePredictor(
        model_clients=[model_client_1, model_client_2, model_client_3]
    )

    # Test with custom weights
    ensemble_custom_weights = EnsemblePredictor(
        model_clients=[model_client_1, model_client_2, model_client_3],
        weights=[0.6, 0.3, 0.1]
    )

    sample_features = {
        "hour_of_day": 9,
        "demand_current_5min": 15.0,
        "is_weekend": 0
    }

    print("--- Ensemble Prediction (Equal Weights) ---")
    for _ in range(5):
        prediction = ensemble_equal_weights.predict(sample_features)
        print(f"Round {_ + 1}: Ensemble Prediction = {prediction:.2f}")
        
    print("\n--- Ensemble Prediction (Custom Weights) ---")
    for _ in range(5):
        prediction = ensemble_custom_weights.predict(sample_features)
        print(f"Round {_ + 1}: Ensemble Prediction = {prediction:.2f}")