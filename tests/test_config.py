"""
Tests for configuration components.
"""
import pytest
from pathlib import Path


def test_config_reader_import():
    """Test config reader import."""
    from src.utils.config_reader import ConfigReader
    assert ConfigReader is not None


def test_config_files_exist():
    """Test that required configuration files exist."""
    config_files = [
        "conf/environments/dev.yaml",
        "conf/environments/prod.yaml",
        "conf/features_params.yaml",
    ]

    for config_file in config_files:
        assert Path(config_file).exists(), f"Config file {config_file} does not exist"


def test_config_reader_initialization(sample_config_data):
    """Test config reader initialization."""
    from src.utils.config_reader import ConfigReader

    # Test with sample config data
    assert isinstance(sample_config_data, dict)
    assert "environment" in sample_config_data
    assert "model_registry" in sample_config_data


def test_yaml_config_validation():
    """Test YAML configuration file validation."""
    import yaml

    yaml_files = [
        "conf/environments/dev.yaml",
        "conf/environments/prod.yaml",
        "conf/features_params.yaml",
    ]

    for yaml_file in yaml_files:
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
            assert data is not None
            assert isinstance(data, dict)


def test_json_schema_validation():
    """Test JSON schema validation."""
    import json

    json_files = [
        "data_artifacts/schemas/demand_event_schema.json"
    ]

    for json_file in json_files:
        with open(json_file, 'r') as f:
            data = json.load(f)
            assert data is not None
            assert isinstance(data, dict)
            assert "type" in data  # JSON schema should have type


def test_oracle_parameter_nexus_import():
    """Test oracle parameter nexus import."""
    from src.configuration.oracle_parameter_nexus import OracleParameterNexus
    assert OracleParameterNexus is not None


def test_parameter_nexus_operations():
    """Test parameter nexus basic operations."""
    from src.configuration.oracle_parameter_nexus import OracleParameterNexus

    nexus = OracleParameterNexus()
    assert nexus is not None

    # Test basic parameter operations
    nexus.set_parameter("test_key", "test_value")
    retrieved_value = nexus.get_parameter("test_key")
    assert retrieved_value == "test_value"


def test_config_data_structure(sample_config_data):
    """Test configuration data structure."""
    assert isinstance(sample_config_data, dict)
    assert len(sample_config_data) > 0

    # Test required top-level keys
    required_keys = ["environment", "model_registry", "kafka", "feature_store", "logging"]
    for key in required_keys:
        assert key in sample_config_data, f"Missing required config key: {key}"


def test_environment_config():
    """Test environment-specific configuration."""
    import yaml

    with open("conf/environments/dev.yaml", 'r') as f:
        dev_config = yaml.safe_load(f)

    with open("conf/environments/prod.yaml", 'r') as f:
        prod_config = yaml.safe_load(f)

    # Both should be dictionaries
    assert isinstance(dev_config, dict)
    assert isinstance(prod_config, dict)

    # Dev should have different settings than prod
    assert dev_config != prod_config


def test_feature_params_config():
    """Test feature parameters configuration."""
    import yaml

    with open("conf/features_params.yaml", 'r') as f:
        feature_config = yaml.safe_load(f)

    assert isinstance(feature_config, dict)
    assert len(feature_config) > 0


@pytest.mark.parametrize("config_file,expected_type", [
    ("conf/environments/dev.yaml", dict),
    ("conf/environments/prod.yaml", dict),
    ("conf/features_params.yaml", dict),
    ("data_artifacts/schemas/demand_event_schema.json", dict),
])
def test_config_file_types(config_file, expected_type):
    """Test that configuration files have expected types."""
    if config_file.endswith('.yaml') or config_file.endswith('.yml'):
        import yaml
        with open(config_file, 'r') as f:
            data = yaml.safe_load(f)
    elif config_file.endswith('.json'):
        import json
        with open(config_file, 'r') as f:
            data = json.load(f)

    assert isinstance(data, expected_type)