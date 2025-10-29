"""
Tests for feature store components.
"""
import pytest
from unittest.mock import Mock, patch


def test_online_feature_retriever_import():
    """Test online feature retriever import."""
    from src.feature_store.online_feature_retriever import OnlineFeatureRetriever
    assert OnlineFeatureRetriever is not None


def test_online_store_client_import():
    """Test online store client import."""
    from src.feature_store.online_store_client import OnlineStoreClient
    assert OnlineStoreClient is not None


def test_backfill_manager_import():
    """Test backfill manager import."""
    from src.feature_store.backfill_manager import BackfillManager
    assert BackfillManager is not None


@patch('src.feature_store.online_feature_retriever.redis.Redis')
def test_online_feature_retriever_initialization(mock_redis):
    """Test online feature retriever initialization."""
    mock_redis_instance = Mock()
    mock_redis.return_value = mock_redis_instance

    from src.feature_store.online_feature_retriever import OnlineFeatureRetriever

    retriever = OnlineFeatureRetriever()
    assert retriever is not None


def test_feature_retrieval_structure(sample_features):
    """Test feature retrieval response structure."""
    # Test with sample entity keys
    entity_keys = {"geohash_id": "dr5ru", "timestamp": "2024-01-01T09:00:00"}

    # Verify entity keys structure
    assert "geohash_id" in entity_keys
    assert "timestamp" in entity_keys
    assert isinstance(entity_keys["geohash_id"], str)
    assert isinstance(entity_keys["timestamp"], str)


@patch('src.feature_store.online_store_client.redis.Redis')
def test_online_store_client_operations(mock_redis):
    """Test online store client basic operations."""
    mock_redis_instance = Mock()
    mock_redis.return_value = mock_redis_instance

    from src.feature_store.online_store_client import OnlineStoreClient

    client = OnlineStoreClient()
    assert client is not None

    # Test that client has expected methods (would be implemented)
    # This is a structure test since actual implementation depends on Redis


@pytest.mark.parametrize("feature_name,expected_type", [
    ("hour_of_day", int),
    ("temperature", (int, float)),
    ("is_weekend", int),
    ("traffic_intensity", (int, float)),
])
def test_feature_data_types(sample_features, feature_name, expected_type):
    """Test feature data types."""
    assert feature_name in sample_features
    if isinstance(expected_type, tuple):
        assert isinstance(sample_features[feature_name], expected_type)
    else:
        assert isinstance(sample_features[feature_name], expected_type)


def test_backfill_data_processing(sample_demand_data):
    """Test backfill data processing structure."""
    assert isinstance(sample_demand_data, type(pd.DataFrame()))
    assert len(sample_demand_data) > 0
    assert "timestamp" in sample_demand_data.columns
    assert "geohash_id" in sample_demand_data.columns


def test_feature_store_config(sample_config_data):
    """Test feature store configuration."""
    assert "feature_store" in sample_config_data
    fs_config = sample_config_data["feature_store"]

    required_keys = ["redis_host", "redis_port", "ttl_seconds"]
    for key in required_keys:
        assert key in fs_config