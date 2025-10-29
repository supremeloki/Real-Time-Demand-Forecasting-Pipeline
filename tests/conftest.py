"""
Test fixtures and configuration for the Real-Time Ride Demand Forecasting Pipeline.

This module provides pytest fixtures that can be used across all test files
to set up common test data, mock objects, and test environments.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any


@pytest.fixture
def sample_demand_data() -> pd.DataFrame:
    """Sample demand data for testing."""
    np.random.seed(42)  # For reproducible tests
    n_samples = 1000

    # Generate time series data
    start_time = datetime(2024, 1, 1)
    timestamps = [start_time + timedelta(hours=i) for i in range(n_samples)]

    data = {
        'timestamp': timestamps,
        'hour_of_day': [ts.hour for ts in timestamps],
        'day_of_week': [ts.weekday() for ts in timestamps],
        'is_weekend': [1 if ts.weekday() >= 5 else 0 for ts in timestamps],
        'is_holiday': [0] * n_samples,  # Assume no holidays for simplicity
        'peak_hour_indicator': [1 if 7 <= ts.hour <= 9 or 17 <= ts.hour <= 19 else 0 for ts in timestamps],
        'demand_last_15min': np.random.poisson(lam=50, size=n_samples),
        'demand_last_30min': np.random.poisson(lam=100, size=n_samples),
        'demand_last_60min': np.random.poisson(lam=200, size=n_samples),
        'demand_last_1440min': np.random.poisson(lam=5000, size=n_samples),
        'temperature': np.random.normal(loc=20, scale=5, size=n_samples),
        'weather_condition': np.random.choice(['clear', 'cloudy', 'rainy'], size=n_samples),
        'traffic_intensity': np.random.uniform(0, 1, size=n_samples),
        'geohash_id': ['dr5ru'] * n_samples,  # Tehran north sample
        'predicted_demand': np.random.poisson(lam=75, size=n_samples)
    }

    return pd.DataFrame(data)


@pytest.fixture
def sample_features() -> Dict[str, Any]:
    """Sample feature dictionary for model testing."""
    return {
        'hour_of_day': 9,
        'day_of_week': 2,
        'is_weekend': 0,
        'is_holiday': 0,
        'peak_hour_indicator': 1,
        'demand_last_15min': 40.0,
        'demand_last_30min': 75.0,
        'demand_last_60min': 150.0,
        'demand_last_1440min': 160.0,
        'temperature': 22.5,
        'weather_condition': 'clear',
        'traffic_intensity': 0.7,
        'geohash_id': 'dr5ru'
    }


@pytest.fixture
def mock_mlflow_tracking_uri():
    """Mock MLflow tracking URI for testing."""
    return "http://localhost:5000"


@pytest.fixture
def sample_model_config() -> Dict[str, Any]:
    """Sample model configuration for testing."""
    return {
        'model_name': 'demand_forecaster_test',
        'model_version': '1.0.0',
        'algorithm': 'xgboost',
        'hyperparameters': {
            'n_estimators': 100,
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8
        },
        'features': [
            'hour_of_day', 'day_of_week', 'is_weekend', 'is_holiday',
            'peak_hour_indicator', 'demand_last_15min', 'demand_last_30min',
            'demand_last_60min', 'demand_last_1440min', 'temperature',
            'weather_condition', 'traffic_intensity'
        ],
        'target': 'predicted_demand'
    }


@pytest.fixture
def sample_api_request() -> Dict[str, Any]:
    """Sample API request payload for testing."""
    return {
        "hour_of_day": 9,
        "day_of_week": 2,
        "is_weekend": 0,
        "is_holiday": 0,
        "peak_hour_indicator": 1,
        "demand_last_15min": 40.0,
        "demand_last_30min": 75.0,
        "demand_last_60min": 150.0,
        "demand_last_1440min": 160.0
    }


@pytest.fixture
def sample_batch_predictions() -> List[Dict[str, Any]]:
    """Sample batch predictions for testing."""
    return [
        {
            "hour_of_day": 9,
            "day_of_week": 2,
            "predicted_demand": 85.5,
            "confidence_score": 0.85
        },
        {
            "hour_of_day": 14,
            "day_of_week": 3,
            "predicted_demand": 65.2,
            "confidence_score": 0.78
        },
        {
            "hour_of_day": 19,
            "day_of_week": 4,
            "predicted_demand": 120.8,
            "confidence_score": 0.92
        }
    ]


@pytest.fixture
def sample_kafka_message() -> Dict[str, Any]:
    """Sample Kafka message for testing."""
    return {
        'timestamp': datetime.now().isoformat(),
        'geohash_id': 'dr5ru',
        'demand_value': 75.5,
        'temperature': 23.4,
        'weather_condition': 'clear',
        'traffic_intensity': 0.6,
        'event_type': 'ride_request'
    }


@pytest.fixture
def sample_config_data() -> Dict[str, Any]:
    """Sample configuration data for testing."""
    return {
        'environment': 'test',
        'model_registry': {
            'uri': 'sqlite:///test.db',
            'model_name': 'demand_forecaster_test'
        },
        'kafka': {
            'bootstrap_servers': ['localhost:9092'],
            'topic': 'test_topic'
        },
        'feature_store': {
            'redis_host': 'localhost',
            'redis_port': 6379,
            'ttl_seconds': 3600
        },
        'logging': {
            'level': 'DEBUG',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    }


@pytest.fixture
def sample_anomaly_data() -> pd.DataFrame:
    """Sample anomaly detection data for testing."""
    np.random.seed(42)
    n_samples = 500

    # Generate normal data
    normal_data = np.random.normal(loc=0, scale=1, size=(n_samples-10, 10))

    # Add some anomalies
    anomalies = np.random.normal(loc=0, scale=5, size=(10, 10))

    # Combine and create timestamps
    all_data = np.vstack([normal_data, anomalies])
    timestamps = [datetime.now() - timedelta(minutes=i) for i in range(n_samples)]

    df = pd.DataFrame(all_data, columns=[f'feature_{i}' for i in range(10)])
    df['timestamp'] = timestamps
    df['is_anomaly'] = [0] * (n_samples-10) + [1] * 10

    return df


@pytest.fixture
def sample_drift_data() -> tuple:
    """Sample data drift detection datasets."""
    np.random.seed(42)

    # Reference data (historical)
    reference_data = np.random.normal(loc=0, scale=1, size=(1000, 5))

    # Current data with slight drift
    current_data = np.random.normal(loc=0.2, scale=1.1, size=(500, 5))

    return reference_data, current_data


@pytest.fixture
def sample_a_b_test_config() -> Dict[str, Any]:
    """Sample A/B testing configuration."""
    return {
        'experiment_name': 'demand_prediction_test',
        'variants': {
            'control': {'model_version': '1.0.0', 'traffic_percentage': 50},
            'treatment': {'model_version': '1.1.0', 'traffic_percentage': 50}
        },
        'metrics': ['rmse', 'mae', 'r2_score'],
        'duration_days': 7,
        'min_sample_size': 1000
    }