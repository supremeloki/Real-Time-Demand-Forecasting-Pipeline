import logging
from typing import Dict, Any, List
import hashlib
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataAnonymizer:
    """
    Provides functions to anonymize sensitive data fields within ride event data,
    ensuring privacy compliance while retaining analytical utility.
    """
    def __init__(self, sensitive_fields: List[str] = None):
        # Default sensitive fields, can be customized
        self.sensitive_fields = sensitive_fields if sensitive_fields else [
            "user_id", "driver_id", "start_location_coords", "end_location_coords",
            "device_id", "ip_address", "phone_number"
        ]
        logging.info(f"DataAnonymizer initialized with sensitive fields: {self.sensitive_fields}")

    def _hash_value(self, value: str) -> str:
        """Applies a cryptographic hash to a string value."""
        return hashlib.sha256(value.encode('utf-8')).hexdigest()

    def _mask_value(self, value: str, mask_char: str = "*", retain_chars: int = 4) -> str:
        """Masks a string value, retaining only a few characters (e.g., for partial visibility)."""
        if len(value) <= retain_chars:
            return mask_char * len(value)
        return value[:retain_chars] + mask_char * (len(value) - retain_chars)

    def anonymize_event(self, event_data: Dict[str, Any], method: str = "hash") -> Dict[str, Any]:
        """
        Anonymizes specified fields in a single event dictionary using the chosen method.
        'hash': Replaces value with its SHA256 hash.
        'mask': Masks most of the value, retaining a few characters.
        'remove': Removes the field entirely.
        """
        anonymized_data = event_data.copy()

        for field in self.sensitive_fields:
            if field in anonymized_data:
                original_value = anonymized_data[field]
                if original_value is None:
                    continue # Skip if value is already None

                if method == "hash":
                    anonymized_data[field] = self._hash_value(str(original_value))
                elif method == "mask":
                    anonymized_data[field] = self._mask_value(str(original_value))
                elif method == "remove":
                    del anonymized_data[field]
                else:
                    logging.warning(f"Unknown anonymization method '{method}' for field '{field}'. Skipping.")
        
        logging.debug(f"Anonymized event data (method: {method}): {anonymized_data}")
        return anonymized_data

    def anonymize_batch(self, batch_events: List[Dict[str, Any]], method: str = "hash") -> List[Dict[str, Any]]:
        """Anonymizes a list of event dictionaries."""
        return [self.anonymize_event(event, method) for event in batch_events]

if __name__ == '__main__':
    anonymizer = DataAnonymizer()

    sample_event = {
        "ride_id": "ride_12345",
        "user_id": "user_abcde",
        "driver_id": "driver_fg789",
        "start_location_coords": {"lat": 35.7, "lon": 51.4},
        "end_location_coords": {"lat": 35.8, "lon": 51.5},
        "pickup_time": "2025-10-19T10:00:00Z",
        "ip_address": "192.168.1.100",
        "fare": 50000,
        "phone_number": "+989123456789"
    }

    print("--- Simulating Data Anonymization ---")

    # Anonymize using hashing
    hashed_event = anonymizer.anonymize_event(sample_event, method="hash")
    print("\n--- Hashed Event ---")
    print(json.dumps(hashed_event, indent=2))

    # Anonymize using masking
    masked_event = anonymizer.anonymize_event(sample_event, method="mask")
    print("\n--- Masked Event ---")
    print(json.dumps(masked_event, indent=2))
    
    # Anonymize by removing
    removed_event = anonymizer.anonymize_event(sample_event, method="remove")
    print("\n--- Removed Fields Event ---")
    print(json.dumps(removed_event, indent=2))

    # Anonymize a batch
    batch_events = [sample_event, {**sample_event, "user_id": "user_xyz", "ride_id": "ride_67890"}]
    hashed_batch = anonymizer.anonymize_batch(batch_events, method="hash")
    print("\n--- Hashed Batch Event (first item) ---")
    print(json.dumps(hashed_batch[0], indent=2))