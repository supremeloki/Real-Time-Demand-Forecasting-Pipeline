import os
import requests
import json
import random
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Add src directory to path for imports
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, 'src'))

from src.utils.config_reader import ConfigReader
from src.utils.logging_setup import setup_logging

logger = setup_logging(__name__)

class LonoABTester:
    """
    A class to manage A/B testing for real-time model inference.
    It directs a percentage of traffic to a challenger model while the rest goes to the champion model.
    """
    def __init__(self, env: str = "dev"):
        self.config = ConfigReader(env)
        
        # Safely get inference API base URL components
        inference_host = self.config.get('inference_api.host', 'localhost')
        inference_port = self.config.get('inference_api.port', 8000)
        self.inference_api_base_url = f"http://{inference_host}:{inference_port}"
        
        logger.info(f"LonoABTester initialized for environment: {env}")
        logger.info(f"Inference API Base URL: {self.inference_api_base_url}")

        self.ab_test_config = self._load_ab_test_config()
        
        self.champion_model_version = self.ab_test_config.get("champion_model_version", "Production")
        self.challenger_model_version = self.ab_test_config.get("challenger_model_version", None)
        self.challenger_traffic_percentage = self.ab_test_config.get("challenger_traffic_percentage", 0.0)

        logger.info(f"A/B Test Config Loaded: Champion='{self.champion_model_version}', "
                    f"Challenger='{self.challenger_model_version}' (Traffic: {self.challenger_traffic_percentage*100}%)")

    def _load_ab_test_config(self) -> Dict[str, Any]:
        """
        Loads the A/B test configuration from 'conf/ab_test_rules.json'.
        Provides default settings if the file is not found or an error occurs.
        """
        config_path = "conf/ab_test_rules.json"
        default_config = {
            "champion_model_version": "Production",
            "challenger_model_version": "Staging",
            "challenger_traffic_percentage": 0.1 # 10% traffic to challenger by default
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    logger.debug(f"A/B test config loaded from {config_path}")
                    # Merge with defaults to ensure all keys exist
                    return {**default_config, **config} 
            else:
                logger.warning(f"A/B test config not found at {config_path}. Using default settings.")
                return default_config
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding A/B test configuration JSON from {config_path}: {e}. Using default settings.")
            return default_config
        except Exception as e:
            logger.error(f"Error loading A/B test configuration from {config_path}: {e}. Using default settings.")
            return default_config

    def _get_model_version_for_request(self) -> str:
        """
        Determines which model version (champion or challenger) to use for the current request
        based on the configured traffic percentage.
        """
        # Only route to challenger if a challenger model is defined and traffic percentage is > 0
        if self.challenger_model_version and self.challenger_traffic_percentage > 0 and \
           random.random() < self.challenger_traffic_percentage:
            logger.debug(f"Routing request to challenger model: {self.challenger_model_version}")
            return self.challenger_model_version
        
        logger.debug(f"Routing request to champion model: {self.champion_model_version}")
        return self.champion_model_version

    def get_prediction(self, features: Dict[str, Any]) -> Optional[float]:
        """
        Sends a prediction request to the inference API, routing to either the champion
        or challenger model based on A/B test configuration.
        """
        model_version_to_use = self._get_model_version_for_request()
        endpoint = f"{self.inference_api_base_url}/predict_single"
        headers = {"Content-Type": "application/json"}
        
        # --- IMPORTANT: Uncommented and activated ---
        # Add a custom header for A/B testing so the inference service can route
        # the request to the correct model version internally.
        headers["X-Model-Version-Override"] = model_version_to_use 
        # --- End of important change ---

        try:
            logger.debug(f"Sending request to {endpoint} with features: {features.keys()} using model version: {model_version_to_use}")
            response = requests.post(endpoint, json=features, headers=headers, timeout=5) # Increased timeout for robustness
            response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
            
            prediction_data = response.json()
            predicted_demand = prediction_data.get("predicted_demand")
            
            if predicted_demand is None:
                logger.warning(f"Prediction response did not contain 'predicted_demand' key. Response: {prediction_data}")
                return None

            logger.info(f"Prediction successful for model version '{model_version_to_use}'. Predicted demand: {predicted_demand}")
            return predicted_demand
        except requests.exceptions.Timeout:
            logger.error(f"Inference API request timed out after 5 seconds for model version {model_version_to_use} at {endpoint}.")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to inference API for A/B test (model version {model_version_to_use}) at {endpoint}: {e}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error from inference API for A/B test (model version {model_version_to_use}) at {endpoint}: {e}. Response: {e.response.text}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"General request error calling inference API for A/B test (model version {model_version_to_use}) at {endpoint}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON response from inference API for model version {model_version_to_use}: {e}. Raw response: {response.text if 'response' in locals() else 'N/A'}")
            return None


    def evaluate_experiment(self, experiment_id: str, metrics: Dict[str, Any]):
        """
        Logs A/B test metrics for a given experiment ID.
        In a production setting, this should integrate with a centralized monitoring
        or experiment tracking system (e.g., MLflow, a database, Kafka, etc.).
        For demonstration, it appends to a local JSON file.
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "experiment_id": experiment_id,
            "metrics": metrics
        }
        
        results_file_path = f"model_experiments/ab_testing/lono_results_{experiment_id}.jsonl" # Changed to .jsonl for line-delimited JSON
        
        try:
            with open(results_file_path, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
            logger.info(f"Logged A/B test metrics for experiment {experiment_id} to {results_file_path}")
            logger.debug(f"Metrics: {metrics}")
        except IOError as e:
            logger.error(f"Error writing A/B test metrics to file {results_file_path}: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while logging A/B test metrics: {e}")

if __name__ == "__main__":
    # Create a dummy config file for testing
    ab_test_rules_path = "conf/ab_test_rules.json"
    os.makedirs(os.path.dirname(ab_test_rules_path), exist_ok=True)
    with open(ab_test_rules_path, "w") as f:
        json.dump({
            "champion_model_version": "Production",
            "challenger_model_version": "Staging",
            "challenger_traffic_percentage": 0.5 # 50% traffic to challenger for testing
        }, f)
    print(f"Created dummy A/B test config at {ab_test_rules_path}")

    ab_tester = LonoABTester(env="dev")
    
    sample_features = {
        "hour_of_day": 8,
        "day_of_week": 1,
        "is_weekend": 0,
        "is_holiday": 0,
        "peak_hour_indicator": 1,
        "demand_last_15min": 30.0,
        "demand_last_30min": 55.0,
        "demand_last_60min": 100.0,
        "demand_last_1440min": 110.0
    }

    print("\nTesting LONO A/B Tester with dummy config...")
    print(f"Inference API Base URL: {ab_tester.inference_api_base_url}")
    print(f"Champion Model: {ab_tester.champion_model_version}, Challenger Model: {ab_tester.challenger_model_version}")
    print(f"Challenger Traffic Percentage: {ab_tester.challenger_traffic_percentage*100}%")

    for i in range(10):
        prediction = ab_tester.get_prediction(sample_features)
        print(f"Request {i+1}: Predicted demand = {prediction}")

    # Simulate logging experiment results
    print("\nSimulating experiment evaluation...")
    ab_tester.evaluate_experiment("demo_run_1", {"conversion_rate": 0.15, "avg_wait_time": 5.2, "model_type": "challenger"})
    ab_tester.evaluate_experiment("demo_run_1", {"conversion_rate": 0.18, "avg_wait_time": 4.8, "model_type": "champion"}) # Example with different metrics

    # Clean up the dummy config file
    if os.path.exists(ab_test_rules_path):
        os.remove(ab_test_rules_path)
        print(f"\nCleaned up dummy A/B test config at {ab_test_rules_path}")
    
    # Clean up dummy results file
    results_file_path = "model_experiments/ab_testing/lono_results_demo_run_1.jsonl"
    if os.path.exists(results_file_path):
        os.remove(results_file_path)
        print(f"Cleaned up dummy A/B test results at {results_file_path}")