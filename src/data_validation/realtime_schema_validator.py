import json
from jsonschema import validate, ValidationError
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class RealtimeSchemaValidator:
    def __init__(
        self, schema_path: str = "data_artifacts/schemas/demand_event_schema.json"
    ):
        try:
            with open(schema_path, "r") as f:
                self.schema = json.load(f)
            logging.info(f"Loaded schema from: {schema_path}")
        except FileNotFoundError:
            logging.error(f"Schema file not found at: {schema_path}")
            self.schema = {}
        except json.JSONDecodeError:
            logging.error(f"Error decoding JSON from schema file: {schema_path}")
            self.schema = {}

    def validate_message(self, message: dict) -> bool:
        if not self.schema:
            logging.warning("No schema loaded, skipping validation.")
            return False
        try:
            validate(instance=message, schema=self.schema)
            logging.debug("Message validated successfully.")
            return True
        except ValidationError as e:
            logging.warning(f"Message validation failed: {e.message}")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred during validation: {e}")
            return False


if __name__ == "__main__":
    validator = RealtimeSchemaValidator()

    # Example valid message
    valid_message = {
        "geohash_id": "dr5ru",
        "timestamp": "2025-10-19T10:30:00Z",
        "request_count": 5,
    }

    # Example invalid message (missing request_count)
    invalid_message = {"geohash_id": "dr5ru", "timestamp": "2025-10-19T10:35:00Z"}

    # Example invalid message (wrong type)
    type_invalid_message = {
        "geohash_id": "dr5ru",
        "timestamp": "2025-10-19T10:35:00Z",
        "request_count": "five",
    }

    print(f"Validating message 1: {validator.validate_message(valid_message)}")
    print(f"Validating message 2: {validator.validate_message(invalid_message)}")
    print(f"Validating message 3: {validator.validate_message(type_invalid_message)}")
