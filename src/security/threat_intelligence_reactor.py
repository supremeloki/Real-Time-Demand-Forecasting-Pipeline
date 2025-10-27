import time
import random
from typing import Dict, Any, List

class ThreatIntelligenceReactor:
    def __init__(self, incident_response_endpoint: str = "http://incident-manager:8080/alert"):
        self._incident_response_endpoint = incident_response_endpoint
        self._threat_database: List[Dict[str, Any]] = []

    def _log_incident(self, incident: Dict[str, Any]):
        print(f"[REACTOR ALERT] {time.time():.2f}: Incident logged: {incident}")

    def _trigger_containment(self, threat_level: str, affected_system: str):
        if threat_level == "CRITICAL":
            print(f"[REACTOR ACTION] Initiating automatic containment for {affected_system}!")
        elif threat_level == "HIGH":
            print(f"[REACTOR ACTION] Escalating to human intervention for {affected_system}.")

    def ingest_threat_report(self, report: Dict[str, Any]):
        self._threat_database.append(report)
        threat_level = report.get("level", "LOW")
        affected_system = report.get("target_system", "unknown")

        self._log_incident(report)
        self._trigger_containment(threat_level, affected_system)

    def review_threat_history(self, limit: int = 10):
        return self._threat_database[-limit:]

if __name__ == '__main__':
    reactor = ThreatIntelligenceReactor()

    print("--- Simulating Threat Intelligence Reaction ---")

    reactor.ingest_threat_report({
        "timestamp": time.time(),
        "level": "MEDIUM",
        "type": "UnauthorizedAccessAttempt",
        "source_ip": "192.168.1.1",
        "target_system": "MLflow-UI"
    })
    time.sleep(0.5)

    reactor.ingest_threat_report({
        "timestamp": time.time(),
        "level": "HIGH",
        "type": "ModelTamperingDetected",
        "model_id": "DemandForecaster_v3",
        "target_system": "ModelRegistry"
    })
    time.sleep(0.5)

    reactor.ingest_threat_report({
        "timestamp": time.time(),
        "level": "CRITICAL",
        "type": "DataExfiltration",
        "data_asset": "CustomerFeatures",
        "target_system": "FeatureStore"
    })

    print("\n--- Threat History ---")
    for report in reactor.review_threat_history():
        print(report)