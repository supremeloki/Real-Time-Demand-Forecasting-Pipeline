import logging
from typing import Dict, Any
from datetime import datetime
import random
import json
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataAccessAuditor:
    """
    Monitors and logs data access attempts to critical ML assets (features, models, predictions).
    Detects suspicious access patterns or unauthorized attempts.
    """
    def __init__(self, audit_log_storage_path: str = "/var/log/snapp_ml/data_access.log",
                 alert_on_failed_attempts: int = 3):
        self.audit_log_storage_path = audit_log_storage_path
        self.alert_on_failed_attempts = alert_on_failed_attempts
        self.failed_attempts_by_user: Dict[str, int] = {}
        logging.info(f"DataAccessAuditor initialized. Logging to {audit_log_storage_path}")

    def _log_audit_event(self, event: Dict[str, Any]):
        """Writes an audit event to a persistent log."""
        try:
            with open(self.audit_log_storage_path, 'a') as f:
                f.write(json.dumps(event) + "\n")
            logging.debug(f"Audit event logged: {event}")
        except IOError as e:
            logging.error(f"Failed to write audit log to {self.audit_log_storage_path}: {e}")

    def audit_access(self,
                     user_id: str,
                     resource_type: str, # e.g., 'feature_store', 'model_registry', 'prediction_api'
                     resource_id: str,   # e.g., 'geohash_id', 'model_name/version'
                     action: str,        # e.g., 'read', 'write', 'predict'
                     is_successful: bool,
                     ip_address: str = "127.0.0.1",
                     details: Dict[str, Any] | None = None):
        """
        Records and audits a data access attempt.
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "ip_address": ip_address,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "is_successful": is_successful,
            "details": details or {}
        }
        self._log_audit_event(event)

        if not is_successful:
            self.failed_attempts_by_user[user_id] = self.failed_attempts_by_user.get(user_id, 0) + 1
            if self.failed_attempts_by_user[user_id] >= self.alert_on_failed_attempts:
                logging.critical(f"SECURITY ALERT: User '{user_id}' has too many failed access attempts "
                                 f"({self.failed_attempts_by_user[user_id]}) on {resource_type}/{resource_id}. Investigate immediately!")
        else:
            # Reset failed attempts on success, or implement more sophisticated logic
            if user_id in self.failed_attempts_by_user:
                del self.failed_attempts_by_user[user_id]

if __name__ == '__main__':
    auditor = DataAccessAuditor(audit_log_storage_path="/tmp/snapp_ml_access.log", alert_on_failed_attempts=3)
    
    # Ensure the log file is clean for a fresh run
    with open("/tmp/snapp_ml_access.log", 'w') as f: pass

    print("--- Simulating Data Access Auditing ---")

    # Simulate legitimate access
    auditor.audit_access("ml_service_account", "feature_store", "dr5ru", "read", True)
    auditor.audit_access("dashboard_user", "prediction_api", "dr5rz", "predict", True)

    # Simulate a user with some failed attempts
    print("\n--- Simulating Failed Attempts Leading to Alert ---")
    for i in range(5):
        is_success = random.random() > 0.7 # Simulate some failures
        auditor.audit_access(
            user_id="suspicious_analyst",
            resource_type="model_registry",
            resource_id="DemandForecaster/2",
            action="update_stage",
            is_successful=is_success,
            ip_address=f"192.168.1.{i+1}"
        )
        time.sleep(0.1)

    # Simulate another legitimate access to clear a previous failure (if any)
    print("\n--- Simulating Successful Access After Failures ---")
    auditor.audit_access("admin_user", "model_registry", "DemandForecaster/2", "read", True)

    print(f"\nAudit log saved to: {auditor.audit_log_storage_path}")
    # You can check the content of /tmp/snapp_ml_access.log