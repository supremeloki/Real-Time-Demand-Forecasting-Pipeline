import logging
import json
from typing import Dict, Any, Tuple, List

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class FeatureSchemaEvolutionManager:
    """
    Manages the evolution of feature schemas over time, providing tools for schema comparison,
    migration planning, and compatibility checks. This is crucial in MLOps for maintaining
    data pipeline stability as features are added, removed, or modified.
    """

    def __init__(
        self,
        current_schema_path: str = "conf/features_params.yaml",
        historical_schema_dir: str = "data_artifacts/schemas/history",
    ):
        self.current_schema_path = current_schema_path
        self.historical_schema_dir = historical_schema_dir
        # Assuming current_schema_path points to a YAML or JSON, load it.
        # For simplicity, we'll use a mock schema or require it to be passed.

        # In a real system, would load 'conf/features_params.yaml' and parse it
        # For this demo, let's just make it clear how it would work.
        logging.info("FeatureSchemaEvolutionManager initialized.")

    def _load_schema_from_path(self, path: str) -> Dict[str, Any]:
        """Loads a schema from a JSON file."""
        try:
            with open(path, "r") as f:
                schema = json.load(f)
            logging.debug(f"Loaded schema from {path}")
            return schema
        except FileNotFoundError:
            logging.error(f"Schema file not found at: {path}")
            return {}
        except json.JSONDecodeError:
            logging.error(f"Error decoding JSON from schema file: {path}")
            return {}
        except Exception as e:
            logging.error(f"Unexpected error loading schema from {path}: {e}")
            return {}

    def compare_schemas(
        self, old_schema: Dict[str, Any], new_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compares two schemas and identifies changes (added, removed, modified features).
        Returns a dictionary detailing the differences.
        """
        differences = {
            "added_features": [],
            "removed_features": [],
            "modified_features": {},
        }

        old_features = set(old_schema.keys())
        new_features = set(new_schema.keys())

        # Added features
        for feature in new_features - old_features:
            differences["added_features"].append(
                {"name": feature, "definition": new_schema[feature]}
            )

        # Removed features
        for feature in old_features - new_features:
            differences["removed_features"].append(
                {"name": feature, "definition": old_schema[feature]}
            )

        # Modified features
        for feature in old_features.intersection(new_features):
            old_def = old_schema[feature]
            new_def = new_schema[feature]

            feature_diff = {}
            for key, old_value in old_def.items():
                if key not in new_def:
                    feature_diff[key] = {"old": old_value, "new": "removed"}
                elif old_value != new_def[key]:
                    feature_diff[key] = {"old": old_value, "new": new_def[key]}

            for key, new_value in new_def.items():
                if key not in old_def:
                    feature_diff[key] = {
                        "old": "added",
                        "new": new_value,
                    }  # New property in existing feature

            if feature_diff:
                differences["modified_features"][feature] = feature_diff

        logging.info(
            f"Schema comparison complete. Found {len(differences['added_features'])} added, "
            f"{len(differences['removed_features'])} removed, and {len(differences['modified_features'])} modified features."
        )
        return differences

    def assess_compatibility(
        self, schema_diff: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Assesses if schema changes are backward-compatible.
        Identifies breaking changes like removing required features or changing types of existing ones.
        """
        breaking_changes = []
        is_compatible = True

        for removed_feature in schema_diff["removed_features"]:
            if removed_feature["definition"].get("required"):
                breaking_changes.append(
                    f"Removed required feature: '{removed_feature['name']}'"
                )
                is_compatible = False

        for feature, changes in schema_diff["modified_features"].items():
            if "type" in changes:
                old_type_def = changes["type"].get("old")
                new_type_def = changes["type"].get("new")
                # More complex type compatibility logic would go here
                # For simplicity, any change to type is breaking if feature is required
                if (
                    old_type_def != "added" and new_type_def != "removed"
                ):  # Not a newly added/removed property
                    # If feature was required, changing its type is a breaking change
                    old_required = self._get_required_status(
                        feature, schema_diff.get("old_schema_snapshot", {})
                    )
                    new_required = self._get_required_status(
                        feature, schema_diff.get("new_schema_snapshot", {})
                    )

                    if (
                        old_required or new_required
                    ):  # If it was or became required, type change is critical
                        breaking_changes.append(
                            f"Type changed for required/critical feature '{feature}': from {old_type_def} to {new_type_def}"
                        )
                        is_compatible = False

        if not is_compatible:
            logging.error(
                f"Schema changes are NOT backward compatible: {breaking_changes}"
            )
        else:
            logging.info("Schema changes appear backward compatible.")

        return is_compatible, breaking_changes

    def _get_required_status(self, feature_name: str, schema: Dict[str, Any]) -> bool:
        """Helper to safely get required status from a schema snapshot."""
        if schema and feature_name in schema:
            return schema[feature_name].get("required", False)
        return False


if __name__ == "__main__":
    manager = FeatureSchemaEvolutionManager()

    # Define a base schema
    base_schema = {
        "geohash_id": {
            "type": "string",
            "required": True,
            "description": "Unique identifier for the geographic area",
        },
        "hour_of_day": {
            "type": "integer",
            "required": True,
            "min_value": 0,
            "max_value": 23,
        },
        "demand_current_5min": {"type": "number", "required": True, "min_value": 0.0},
        "is_weekend": {"type": "integer", "allowed_values": [0, 1]},
        "temperature_celsius": {
            "type": "number",
            "min_value": -50,
            "max_value": 50,
            "required": False,
        },
    }

    # Scenario 1: Backward-compatible change (add optional feature)
    new_schema_compatible = base_schema.copy()
    new_schema_compatible["precipitation_mm"] = {
        "type": "number",
        "min_value": 0.0,
        "required": False,
    }
    new_schema_compatible["hour_of_day"] = {
        "type": "integer",
        "required": True,
        "min_value": 0,
        "max_value": 23,
        "unit": "hours",
    }  # Added a property

    print(
        "--- Scenario 1: Compatible Change (Add optional feature, add property to existing) ---"
    )
    diff_comp = manager.compare_schemas(base_schema, new_schema_compatible)
    print("Differences:", json.dumps(diff_comp, indent=2))
    is_comp, breaking_comp = manager.assess_compatibility(diff_comp)
    print(f"Is Compatible: {is_comp}, Breaking Changes: {breaking_comp}\n")

    # Scenario 2: Breaking change (remove required feature)
    new_schema_breaking_removed = base_schema.copy()
    del new_schema_breaking_removed["geohash_id"]  # Remove a required feature

    print("--- Scenario 2: Breaking Change (Remove Required Feature) ---")
    diff_break_removed = manager.compare_schemas(
        base_schema, new_schema_breaking_removed
    )
    # Inject schema snapshots for assessment
    diff_break_removed["old_schema_snapshot"] = base_schema
    diff_break_removed["new_schema_snapshot"] = new_schema_breaking_removed

    print("Differences:", json.dumps(diff_break_removed, indent=2))
    is_comp, breaking_comp = manager.assess_compatibility(diff_break_removed)
    print(f"Is Compatible: {is_comp}, Breaking Changes: {breaking_comp}\n")

    # Scenario 3: Breaking change (change type of required feature)
    new_schema_breaking_type = base_schema.copy()
    new_schema_breaking_type["hour_of_day"] = {
        "type": "string",
        "required": True,
        "allowed_values": ["morning", "afternoon", "evening"],
    }

    print("--- Scenario 3: Breaking Change (Change Type of Required Feature) ---")
    diff_break_type = manager.compare_schemas(base_schema, new_schema_breaking_type)
    # Inject schema snapshots for assessment
    diff_break_type["old_schema_snapshot"] = base_schema
    diff_break_type["new_schema_snapshot"] = new_schema_breaking_type

    print("Differences:", json.dumps(diff_break_type, indent=2))
    is_comp, breaking_comp = manager.assess_compatibility(diff_break_type)
    print(f"Is Compatible: {is_comp}, Breaking Changes: {breaking_comp}\n")
