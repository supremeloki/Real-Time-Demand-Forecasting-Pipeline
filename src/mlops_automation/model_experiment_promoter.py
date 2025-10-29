import logging
from typing import Dict, Any, List
import mlflow
import os
import random
from datetime import datetime

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class ModelExperimentPromoter:
    """
    Automates the evaluation and promotion of new model experiments to production or staging,
    and manages A/B test configurations.
    """

    def __init__(self, mlflow_tracking_uri: str = "http://localhost:5000"):
        os.environ["MLFLOW_TRACKING_URI"] = mlflow_tracking_uri
        self.mlflow_client = mlflow.tracking.MlflowClient()
        logging.info(
            f"ModelExperimentPromoter initialized with MLflow tracking: {mlflow_tracking_uri}"
        )

    def _get_model_metrics(self, model_version_uri: str) -> Dict[str, Any]:
        """Fetches evaluation metrics for a given model version from MLflow."""
        try:
            # Parse model name and version from URI like "models:/DemandForecaster/1"
            parts = model_version_uri.split("/")
            model_name = parts[-2]
            version = parts[-1]

            model_version = self.mlflow_client.get_model_version(model_name, version)
            run = self.mlflow_client.get_run(model_version.run_id)
            metrics = run.data.metrics
            logging.debug(f"Fetched metrics for {model_version_uri}: {metrics}")
            return metrics
        except Exception as e:
            logging.error(f"Failed to fetch metrics for {model_version_uri}: {e}")
            return {}

    def _evaluate_candidate_model(
        self, candidate_model_uri: str, production_model_uri: str
    ) -> bool:
        """
        Compares candidate model's performance to the current production model.
        Returns True if candidate is better.
        """
        candidate_metrics = self._get_model_metrics(candidate_model_uri)
        prod_metrics = self._get_model_metrics(production_model_uri)

        candidate_rmse = candidate_metrics.get("val_rmse", float("inf"))
        prod_rmse = prod_metrics.get("val_rmse", float("inf"))

        logging.info(f"Candidate ({candidate_model_uri}) RMSE: {candidate_rmse:.2f}")
        logging.info(f"Production ({production_model_uri}) RMSE: {prod_rmse:.2f}")

        if candidate_rmse < prod_rmse * 0.95:  # Candidate must be significantly better
            logging.info("Candidate model shows significant performance improvement.")
            return True
        elif candidate_rmse < prod_rmse * 0.99:
            logging.info(
                "Candidate model shows slight improvement, consider for A/B testing."
            )
            return True  # Still consider for A/B test
        else:
            logging.info("Candidate model does not show sufficient improvement.")
            return False

    def promote_to_staging(self, model_name: str, version: int):
        """Promotes a specific model version to the 'Staging' stage in MLflow."""
        self.mlflow_client.transition_model_version_stage(
            name=model_name, version=version, stage="Staging"
        )
        logging.info(f"Model {model_name} version {version} transitioned to Staging.")

    def promote_to_production(self, model_name: str, version: int):
        """Promotes a specific model version to the 'Production' stage in MLflow."""
        # First, archive the current production model
        for mv in self.mlflow_client.search_model_versions(f"name='{model_name}'"):
            if mv.current_stage == "Production":
                logging.info(
                    f"Archiving current Production model {model_name} version {mv.version}."
                )
                self.mlflow_client.transition_model_version_stage(
                    name=model_name, version=mv.version, stage="Archived"
                )

        self.mlflow_client.transition_model_version_stage(
            name=model_name, version=version, stage="Production"
        )
        logging.info(
            f"Model {model_name} version {version} transitioned to Production."
        )

    def update_ab_test_config(
        self, experiment_id: str, traffic_split: Dict[str, float]
    ):
        """
        Simulates updating an A/B testing configuration for traffic routing.
        In a real system, this would update a feature flag service or config management system.
        """
        logging.info(
            f"Updating A/B test '{experiment_id}' with traffic split: {traffic_split}"
        )
        # Placeholder for actual config update (e.g., to a Redis cache or ConfigMap)
        self.ab_test_configs[experiment_id] = {
            "traffic_split": traffic_split,
            "last_updated": datetime.now().isoformat(),
        }
        logging.info(f"A/B test config for '{experiment_id}' updated (simulated).")

    # Mock A/B test configs for demonstration
    ab_test_configs = {}


if __name__ == "__main__":
    # Ensure MLflow server is running (e.g., `mlflow ui`) for this to work with real MLflow
    # For local demo, `mlflow server --backend-store-uri sqlite:///mlruns.db --default-artifact-root ./mlruns_artifacts`
    promoter = ModelExperimentPromoter(
        mlflow_tracking_uri="sqlite:///mlruns.db"
    )  # Use local path for demo

    model_name = "DemandForecaster"

    # --- Simulate a new model version being trained and logged ---
    # In a real scenario, this would come from the `train.py` script
    logging.info("\n--- Simulating Model Training and Logging ---")
    with mlflow.start_run(run_name="candidate_train_run"):
        mlflow.log_param("n_estimators", 100)
        mlflow.log_metric("val_rmse", random.uniform(8.0, 12.0))
        mlflow.log_metric("val_mae", random.uniform(5.0, 8.0))
        # Imagine model artifact is logged here
        mlflow.pyfunc.log_model(
            python_model=mlflow.pyfunc.PythonModel(),  # Dummy model
            artifact_path="model",
            registered_model_name=model_name,
        )
    candidate_version = promoter.mlflow_client.search_model_versions(
        f"name='{model_name}'"
    )[-1].version
    logging.info(f"New model version {candidate_version} created.")

    # Assume a production model already exists (for comparison)
    # This might fail if no previous model is in Production, for demo purposes, assume it exists.
    try:
        current_prod_version_obj = [
            mv
            for mv in promoter.mlflow_client.search_model_versions(
                f"name='{model_name}'"
            )
            if mv.current_stage == "Production"
        ]
        if not current_prod_version_obj:
            # Manually create a dummy production version for demo if none exists
            logging.warning(
                "No Production model found. Creating a dummy one for comparison."
            )
            promoter.mlflow_client.transition_model_version_stage(
                name=model_name,
                version=candidate_version,  # Promote the first candidate as dummy prod
                stage="Production",
            )
            promoter.mlflow_client.log_metric(
                run_id=promoter.mlflow_client.get_model_version(
                    name=model_name, version=candidate_version
                ).run_id,
                key="val_rmse",
                value=10.0,
            )
            promoter.mlflow_client.log_metric(
                run_id=promoter.mlflow_client.get_model_version(
                    name=model_name, version=candidate_version
                ).run_id,
                key="val_mae",
                value=7.0,
            )

        current_prod_model_uri = f"models:/{model_name}/Production"
        candidate_model_uri = f"models:/{model_name}/{candidate_version}"

        logging.info("\n--- Evaluating Candidate Model ---")
        is_better = promoter._evaluate_candidate_model(
            candidate_model_uri, current_prod_model_uri
        )
        if is_better:
            print(
                f"\nCandidate version {candidate_version} is better. Promoting to Staging..."
            )
            promoter.promote_to_staging(model_name, candidate_version)

            # Simulate A/B test setup for new staging model
            print("\n--- Setting up A/B Test for Staging Model ---")
            promoter.update_ab_test_config(
                experiment_id="demand_forecast_ab_test_v1",
                traffic_split={"Production": 0.9, f"Staging_v{candidate_version}": 0.1},
            )
            print("A/B Test configured with 10% traffic to Staging.")

            # Simulate evaluation of A/B test results and full promotion
            if random.random() > 0.7:  # Simulate successful A/B test
                print("\n--- A/B Test successful! Promoting Staging to Production ---")
                promoter.promote_to_production(model_name, candidate_version)
                promoter.update_ab_test_config(
                    experiment_id="demand_forecast_ab_test_v1",
                    traffic_split={f"Production": 1.0},  # New model is now 100% prod
                )
                print("New model fully promoted and A/B test retired.")
            else:
                print(
                    "\nA/B Test did not show significant improvement or had issues. Staging model not promoted to Production."
                )
        else:
            print("\nCandidate model not significantly better. No promotion.")
    except Exception as e:
        logging.error(
            f"Error in main block: {e}. Please ensure MLflow is running and some models exist."
        )
        print(
            "\nNote: For a fully functional demo, ensure MLflow is running and a 'DemandForecaster' model exists with a 'Production' version."
        )
