import time
import random
import json
from typing import Any


class OracleParameterNexus:
    def __init__(self, initial_params: dict):
        self._parameters = initial_params
        self._last_update_time = time.time()

    def get_parameter(self, param_key: str, default_value: Any = None):
        return self._parameters.get(param_key, default_value)

    def set_parameter(self, param_key: str, param_value: Any):
        self._parameters[param_key] = param_value
        self._last_update_time = time.time()

    def refresh_from_source(self, new_params: dict):
        self._parameters.update(new_params)
        self._last_update_time = time.time()

    def get_status(self):
        return {
            "parameters_count": len(self._parameters),
            "last_updated": self._last_update_time,
        }


if __name__ == "__main__":
    initial_config = {
        "model_learning_rate": 0.01,
        "feature_toggle_beta_ui": False,
        "api_timeout_ms": 2000,
    }
    nexus = OracleParameterNexus(initial_config)

    print(f"Current learning rate: {nexus.get_parameter('model_learning_rate')}")
    print(f"Beta UI enabled: {nexus.get_parameter('feature_toggle_beta_ui')}")

    nexus.set_parameter("feature_toggle_beta_ui", True)
    print(f"Beta UI enabled after set: {nexus.get_parameter('feature_toggle_beta_ui')}")

    new_updates = {
        "api_timeout_ms": 3000,
        "model_learning_rate": 0.005,
        "new_experimental_param": "alpha_value",
    }
    nexus.refresh_from_source(new_updates)

    print(f"Updated config status: {nexus.get_status()}")
    print(f"New experimental param: {nexus.get_parameter('new_experimental_param')}")
