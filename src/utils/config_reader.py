import yaml
import os

class ConfigReader:
    def __init__(self, env: str = "dev"):
        self.env = env
        self.base_path = "conf"
        self.config = self._load_config()

    def _load_config(self):
        env_config_path = os.path.join(self.base_path, "environments", f"{self.env}.yaml")
        features_params_path = os.path.join(self.base_path, "features_params.yaml")

        config = {}
        with open(env_config_path, 'r') as f:
            config.update(yaml.safe_load(f))
        with open(features_params_path, 'r') as f:
            config.update({'features_params': yaml.safe_load(f)})
        return config

    def get(self, key: str, default=None):
        keys = key.split('.')
        val = self.config
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val