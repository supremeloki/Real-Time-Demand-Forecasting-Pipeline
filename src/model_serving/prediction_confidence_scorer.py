import logging
from typing import Dict, Any, List
import numpy as np
from scipy.stats import iqr # Interquartile range for robust spread estimation

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PredictionConfidenceScorer:
    """
    Attaches a confidence score to a model's prediction, based on prediction variance
    from an ensemble or historical prediction error.
    """
    def __init__(self, historical_error_std: float = 5.0, confidence_threshold: float = 0.7):
        self.historical_error_std = historical_error_std 
        self.confidence_threshold = confidence_threshold 
        logging.info(f"PredictionConfidenceScorer initialized with historical_error_std={historical_error_std}")

    def score_ensemble_confidence(self, individual_predictions: List[float]) -> Dict[str, Any]:
        """
        Calculates confidence based on the spread of predictions from an ensemble.
        A smaller spread implies higher confidence.
        """
        if not individual_predictions or len(individual_predictions) < 2:
            logging.warning("Insufficient individual predictions for ensemble confidence scoring. Returning default.")
            return {"confidence_score": 0.5, "confidence_level": "MEDIUM", "prediction_spread": 0.0}

        predictions_array = np.array(individual_predictions)
        prediction_spread = iqr(predictions_array)
        normalized_spread = prediction_spread / (self.historical_error_std * 2) # Factor of 2 for reasonable scale
        confidence_score = max(0.0, 1.0 - min(1.0, normalized_spread)) # Clamp between 0 and 1

        confidence_level = "MEDIUM"
        if confidence_score >= self.confidence_threshold:
            confidence_level = "HIGH"
        elif confidence_score < (1.0 - self.confidence_threshold):
            confidence_level = "LOW"
            logging.warning(f"Low confidence prediction detected. Spread: {prediction_spread:.2f}, Score: {confidence_score:.2f}")

        return {
            "confidence_score": round(confidence_score, 3),
            "confidence_level": confidence_level,
            "prediction_spread": round(prediction_spread, 2)
        }
    
    def score_model_confidence_single(self, prediction: float, recent_errors: List[float]) -> Dict[str, Any]:
        """
        Calculates confidence for a single model prediction based on recent historical errors.
        This is a simpler approach for non-ensemble models.
        """
        if not recent_errors or len(recent_errors) < 5: # Need a few errors to estimate variance
            logging.warning("Insufficient recent errors for single model confidence scoring. Returning default.")
            return {"confidence_score": 0.5, "confidence_level": "MEDIUM", "error_variability": self.historical_error_std}

        current_error_std = np.std(recent_errors)

        variability_ratio = current_error_std / self.historical_error_std
        
        confidence_score = max(0.0, 1.0 - min(1.0, variability_ratio - 0.5)) # Adjust for reasonable scaling

        confidence_level = "MEDIUM"
        if confidence_score >= self.confidence_threshold:
            confidence_level = "HIGH"
        elif confidence_score < (1.0 - self.confidence_threshold):
            confidence_level = "LOW"
            logging.warning(f"Low confidence prediction detected. Error variability: {current_error_std:.2f}, Score: {confidence_score:.2f}")

        return {
            "confidence_score": round(confidence_score, 3),
            "confidence_level": confidence_level,
            "error_variability": round(current_error_std, 2)
        }


if __name__ == '__main__':
    scorer = PredictionConfidenceScorer(historical_error_std=7.0, confidence_threshold=0.8)

    print("--- Simulating Ensemble Confidence Scoring ---")
    # High confidence scenario (low spread)
    preds_high_conf = [50.1, 49.8, 50.5, 49.9, 50.3]
    conf_high = scorer.score_ensemble_confidence(preds_high_conf)
    print(f"Predictions: {preds_high_conf} -> {conf_high}")

    # Low confidence scenario (high spread)
    preds_low_conf = [40.0, 65.0, 50.0, 55.0, 48.0]
    conf_low = scorer.score_ensemble_confidence(preds_low_conf)
    print(f"Predictions: {preds_low_conf} -> {conf_low}")

    print("\n--- Simulating Single Model Confidence Scoring ---")
    # Recent errors for high confidence
    recent_errs_high_conf = [1.2, -0.8, 0.5, 2.1, -1.5, 0.9, -0.3, 1.8]
    conf_single_high = scorer.score_model_confidence_single(prediction=50.0, recent_errors=recent_errs_high_conf)
    print(f"Recent Errors: {recent_errs_high_conf} -> {conf_single_high}")

    # Recent errors for low confidence (higher variability)
    recent_errs_low_conf = [5.0, -10.0, 2.0, 15.0, -8.0, 3.0, -12.0, 6.0]
    conf_single_low = scorer.score_model_confidence_single(prediction=50.0, recent_errors=recent_errs_low_conf)
    print(f"Recent Errors: {recent_errs_low_conf} -> {conf_single_low}")