"""
Tests for model serving components.
"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


def test_api_app_import():
    """Test that the FastAPI app can be imported."""
    from src.model_serving.api_app import app
    assert app is not None
    assert hasattr(app, 'routes')


def test_prediction_logic_import():
    """Test prediction logic components."""
    import src.model_serving.prediction_logic as pl
    assert pl is not None


@patch('src.model_serving.prediction_logic.joblib.load')
@patch('src.model_serving.prediction_logic.mlflow.pyfunc.load_model')
def test_prediction_logic_initialization(mock_mlflow_load, mock_joblib_load):
    """Test prediction logic initialization with mocked dependencies."""
    mock_mlflow_load.return_value = Mock()
    mock_joblib_load.return_value = Mock()

    from src.model_serving.prediction_logic import PredictionLogic

    # This should not raise an exception
    predictor = PredictionLogic()
    assert predictor is not None


def test_ensemble_predictor_import():
    """Test ensemble predictor import."""
    from src.model_serving.ensemble_predictor import EnsemblePredictor
    assert EnsemblePredictor is not None


def test_explainability_service_import():
    """Test explainability service import."""
    import src.model_serving.explainability_service as es
    assert es is not None


def test_prediction_confidence_scorer_import():
    """Test prediction confidence scorer import."""
    from src.model_serving.prediction_confidence_scorer import PredictionConfidenceScorer
    assert PredictionConfidenceScorer is not None


def test_regional_model_manager_import():
    """Test regional model manager import."""
    from src.model_serving.regional_model_manager import RegionalModelManager
    assert RegionalModelManager is not None


@pytest.mark.parametrize("expected_keys", [
    ["prediction", "confidence"],
    ["prediction", "confidence"],
])
def test_prediction_response_structure(sample_features, expected_keys):
    """Test that prediction responses have expected structure."""
    # This is a structure test - actual implementation would need mocking
    assert isinstance(sample_features, dict)
    assert len(sample_features) > 0

    # Test that expected keys are present in our sample data
    for key in ["hour_of_day", "day_of_week"]:
        assert key in sample_features


def test_api_request_validation(sample_api_request):
    """Test API request validation with sample data."""
    required_fields = [
        "hour_of_day", "day_of_week", "is_weekend", "is_holiday",
        "peak_hour_indicator", "demand_last_15min", "demand_last_30min",
        "demand_last_60min", "demand_last_1440min"
    ]

    for field in required_fields:
        assert field in sample_api_request
        assert isinstance(sample_api_request[field], (int, float))


def test_batch_predictions_structure(sample_batch_predictions):
    """Test batch predictions structure."""
    assert isinstance(sample_batch_predictions, list)
    assert len(sample_batch_predictions) > 0

    for prediction in sample_batch_predictions:
        assert "predicted_demand" in prediction
        assert "confidence_score" in prediction
        assert isinstance(prediction["predicted_demand"], (int, float))
        assert isinstance(prediction["confidence_score"], (int, float))
        assert 0 <= prediction["confidence_score"] <= 1