import sys
import os
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, 'src'))

import logging
from typing import Dict, Any, Callable
import mlflow
import optuna
import pandas as pd
import numpy as np
import xgboost as xgb

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HyperparameterOptimizer:
    def __init__(self, 
                 model_trainer: Callable[[Dict[str, Any]], float], # A function that trains a model and returns a metric
                 search_space: Dict[str, Any],
                 experiment_name: str = "DemandForecastingHPO",
                 num_trials: int = 50):
        
        self.model_trainer = model_trainer
        self.search_space = search_space
        self.experiment_name = experiment_name
        self.num_trials = num_trials
        
        # Ensure MLflow tracking is configured
        # For local, it might be http://localhost:5000 or a local file path
        if "MLFLOW_TRACKING_URI" not in os.environ:
             logging.warning("MLFLOW_TRACKING_URI environment variable not set. Using default local MLflow tracking.")
             mlflow.set_tracking_uri("sqlite:///mlruns.db") # Default for local demo
        
        mlflow.set_experiment(experiment_name)
        logging.info(f"HyperparameterOptimizer initialized for experiment '{experiment_name}'.")

    def _objective(self, trial: optuna.Trial) -> float:
        """
        Optuna objective function to be minimized (e.g., RMSE).
        """
        params = {}
        for param_name, config in self.search_space.items():
            param_type = config['type']
            if param_type == 'int':
                params[param_name] = trial.suggest_int(param_name, config['low'], config['high'], step=config.get('step', 1))
            elif param_type == 'float':
                params[param_name] = trial.suggest_float(param_name, config['low'], config['high'], log=config.get('log', False))
            elif param_type == 'categorical':
                params[param_name] = trial.suggest_categorical(param_name, config['choices'])
            # Add more types as needed
        
        with mlflow.start_run(run_name=f"trial_{trial.number}"):
            mlflow.log_params(params)
            metric_value = self.model_trainer(params) # Call the external trainer function
            mlflow.log_metric("validation_metric", metric_value)
            return metric_value

    def run_optimization(self) -> Dict[str, Any]:
        """
        Executes the hyperparameter optimization using Optuna.
        """
        logging.info(f"Starting hyperparameter optimization with {self.num_trials} trials...")
        study = optuna.create_study(direction="minimize", study_name=self.experiment_name)
        study.optimize(self._objective, n_trials=self.num_trials)

        logging.info("Optimization finished.")
        logging.info(f"Best trial: {study.best_trial.number}")
        logging.info(f"Best value (RMSE): {study.best_value:.4f}")
        logging.info(f"Best hyperparameters: {study.best_params}")
        
        return study.best_params

if __name__ == '__main__':
    # --- Mock Model Trainer Function ---
    def mock_xgboost_trainer(params: Dict[str, Any]) -> float:
        """
        A mock function that simulates training an XGBoost model and returning RMSE.
        In a real scenario, this would load data, train XGBoost, evaluate, and return a metric.
        """
        logging.info(f"Mock training with params: {params}")
        # Simulate data loading
        X = pd.DataFrame(np.random.rand(100, 5), columns=[f'feat_{i}' for i in range(5)])
        y = pd.Series(np.random.rand(100) * 100)

        # Simulate training time and varying performance based on params
        rmse = np.random.uniform(5, 20) # Base RMSE
        if params.get('n_estimators', 100) > 150: rmse *= 0.9 # Better n_estimators
        if params.get('learning_rate', 0.1) < 0.05: rmse *= 1.1 # Worse learning rate
        
        logging.info(f"Mock training complete. Simulated RMSE: {rmse:.4f}")
        return rmse

    # Define a simple search space
    hp_search_space = {
        "n_estimators": {"type": "int", "low": 50, "high": 200, "step": 50},
        "learning_rate": {"type": "float", "low": 0.01, "high": 0.3, "log": True},
        "max_depth": {"type": "int", "low": 3, "high": 9},
        "subsample": {"type": "float", "low": 0.6, "high": 1.0},
        "colsample_bytree": {"type": "float", "low": 0.6, "high": 1.0}
    }

    optimizer = HyperparameterOptimizer(
        model_trainer=mock_xgboost_trainer,
        search_space=hp_search_space,
        num_trials=10 # Reduced for quick demo
    )

    print("--- Running Hyperparameter Optimization ---")
    best_params = optimizer.run_optimization()
    print("\nBest Hyperparameters Found:")
    for param, value in best_params.items():
        print(f"  {param}: {value}")

    print("\nCheck MLflow UI (e.g., http://localhost:5000) for detailed experiment results.")