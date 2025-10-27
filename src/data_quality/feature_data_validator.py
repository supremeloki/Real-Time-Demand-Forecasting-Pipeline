import pandas as pd
import logging
from typing import Dict, Any, List, Union, Type

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FeatureDataValidator:
    """
    Validates incoming feature data against predefined rules.
    """
    def __init__(self, schema: Dict[str, Dict[str, Any]]):
        self.schema = schema
        logging.info("FeatureDataValidator initialized with schema.")

    def validate_features(self, features: Dict[str, Any]) -> List[str]:
        """
        Validates a single set of features.
        Returns a list of error messages, or an empty list if valid.
        """
        errors = []
        for feature_name, rules in self.schema.items():
            value = features.get(feature_name)

            # Check for required fields
            if rules.get('required', False) and value is None:
                errors.append(f"Missing required feature: '{feature_name}'")
                continue # Skip further checks for this feature if missing

            if value is not None:
                type_check_failed = False
                # Check data type
                expected_type: Union[Type, tuple[Type, ...], None] = rules.get('type')
                if expected_type:
                    if not isinstance(value, expected_type):
                        if isinstance(expected_type, tuple):
                            expected_type_names = ", ".join([t.__name__ for t in expected_type])
                            errors.append(f"Invalid type for '{feature_name}': Expected one of ({expected_type_names}), got {type(value).__name__}")
                        else:
                            errors.append(f"Invalid type for '{feature_name}': Expected {expected_type.__name__}, got {type(value).__name__}")
                        type_check_failed = True

                if not type_check_failed: # Only proceed with numerical/allowed value checks if type is correct
                    # Check min_value
                    min_value = rules.get('min_value')
                    if min_value is not None and value < min_value:
                        errors.append(f"Value for '{feature_name}' ({value}) is below min_value ({min_value})")

                    # Check max_value
                    max_value = rules.get('max_value')
                    if max_value is not None and value > max_value:
                        errors.append(f"Value for '{feature_name}' ({value}) is above max_value ({max_value})")

                    # Check allowed_values
                    allowed_values = rules.get('allowed_values')
                    if allowed_values is not None and value not in allowed_values:
                        errors.append(f"Value for '{feature_name}' ({value}) is not in allowed_values: {allowed_values}")
        
        if errors:
            logging.warning(f"Feature validation failed with {len(errors)} errors.")
        else:
            logging.debug("Feature validation successful.")
        return errors

if __name__ == '__main__':
    feature_schema = {
        "geohash_id": {"type": str, "required": True},
        "hour_of_day": {"type": int, "required": True, "min_value": 0, "max_value": 23},
        "demand_current_5min": {"type": float, "required": True, "min_value": 0.0},
        "is_weekend": {"type": int, "allowed_values": [0, 1]},
        "temperature_celsius": {"type": (int, float), "min_value": -50, "max_value": 50, "required": False}
    }

    validator = FeatureDataValidator(feature_schema)

    print("--- Simulating Feature Data Validation ---")

    valid_features = {
        "geohash_id": "dr5ru",
        "hour_of_day": 10,
        "demand_current_5min": 25.5,
        "is_weekend": 0,
        "temperature_celsius": 15.0
    }
    errors = validator.validate_features(valid_features)
    print(f"\nValidation for valid_features (Expected: No errors):\nErrors: {errors}")

    invalid_features = {
        "geohash_id": "dr5rz",
        "hour_of_day": 30, # Out of range
        "demand_current_5min": -5.0, # Below min_value
        "is_weekend": 2, # Not in allowed_values
    }
    errors = validator.validate_features(invalid_features)
    print(f"\nValidation for invalid_features (Expected: Errors):\nErrors: {errors}")

    missing_features = {
        "hour_of_day": 12,
        "demand_current_5min": 10.0
    }
    errors = validator.validate_features(missing_features)
    print(f"\nValidation for missing_features (Expected: Missing geohash_id):\nErrors: {errors}")

    type_error_features = {
        "geohash_id": "dr5r7",
        "hour_of_day": "ten", # Incorrect type
        "demand_current_5min": 12.3,
        "is_weekend": 0
    }
    errors = validator.validate_features(type_error_features)
    print(f"\nValidation for type_error_features (Expected: Type error for hour_of_day):\nErrors: {errors}")
    
    # Test with temperature_celsius as int
    temp_int_features = {
        "geohash_id": "dr5r7",
        "hour_of_day": 10,
        "demand_current_5min": 12.3,
        "is_weekend": 0,
        "temperature_celsius": 20
    }
    errors = validator.validate_features(temp_int_features)
    print(f"\nValidation for temp_int_features (Expected: No errors):\nErrors: {errors}")