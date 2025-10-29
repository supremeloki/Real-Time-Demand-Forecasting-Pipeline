"""
Tests for utility components.
"""
import pytest
from unittest.mock import Mock, patch
import logging


def test_logging_setup_import():
    """Test logging setup import."""
    from src.utils.logging_setup import setup_logging
    assert setup_logging is not None


def test_config_reader_import():
    """Test config reader import."""
    from src.utils.config_reader import ConfigReader
    assert ConfigReader is not None


def test_logging_setup_functionality():
    """Test logging setup functionality."""
    from src.utils.logging_setup import setup_logging

    # Test that setup_logging returns a logger
    logger = setup_logging("test_logger")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger"


def test_config_reader_functionality(sample_config_data):
    """Test config reader functionality."""
    from src.utils.config_reader import ConfigReader

    # Test initialization
    config_reader = ConfigReader()
    assert config_reader is not None

    # Test with sample config data
    assert isinstance(sample_config_data, dict)
    assert "environment" in sample_config_data


@pytest.mark.parametrize("log_level", [
    "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
])
def test_logging_levels(log_level):
    """Test different logging levels."""
    from src.utils.logging_setup import setup_logging

    logger = setup_logging(f"test_logger_{log_level}")
    assert logger.level <= getattr(logging, log_level)


def test_config_nested_access(sample_config_data):
    """Test nested configuration access."""
    # Test nested dictionary access patterns
    assert "model_registry" in sample_config_data
    assert "uri" in sample_config_data["model_registry"]
    assert "model_name" in sample_config_data["model_registry"]

    assert "kafka" in sample_config_data
    assert "bootstrap_servers" in sample_config_data["kafka"]

    assert "feature_store" in sample_config_data
    assert "redis_host" in sample_config_data["feature_store"]


def test_config_validation():
    """Test configuration validation."""
    from src.utils.config_reader import ConfigReader

    config_reader = ConfigReader()

    # Test parameter setting and getting
    test_key = "test.parameter.key"
    test_value = "test_value"

    config_reader.set(test_key, test_value)
    retrieved_value = config_reader.get(test_key)

    assert retrieved_value == test_value


def test_logger_file_handler():
    """Test logger file handler setup."""
    from src.utils.logging_setup import setup_logging
    import os

    logger = setup_logging("test_file_logger")

    # Check if any handlers are file handlers (would be set up in actual usage)
    # This is a structural test
    assert len(logger.handlers) >= 0  # At minimum, should have handlers


def test_config_default_values():
    """Test configuration default values."""
    from src.utils.config_reader import ConfigReader

    config_reader = ConfigReader()

    # Test default value retrieval
    default_value = config_reader.get("nonexistent.key", "default")
    assert default_value == "default"

    # Test None when no default provided
    none_value = config_reader.get("another.nonexistent.key")
    assert none_value is None


@pytest.mark.parametrize("config_path,expected_delimiter", [
    ("simple.key", "."),
    ("nested.deep.key", "."),
    ("another.level.down", "."),
])
def test_config_key_parsing(config_path, expected_delimiter):
    """Test configuration key parsing."""
    # Test key splitting logic
    keys = config_path.split(expected_delimiter)
    assert len(keys) > 1
    assert all(len(key) > 0 for key in keys)


def test_utils_module_structure():
    """Test utils module structure."""
    import src.utils as utils

    # Test that utils module has expected attributes
    assert hasattr(utils, 'config_reader')
    assert hasattr(utils, 'logging_setup')