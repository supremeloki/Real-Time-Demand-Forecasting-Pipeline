import time
import random
from typing import Dict, Any, List


class CelestialAlignmentEngine:
    def __init__(self, core_components: List[str]):
        self._component_health: Dict[str, str] = {
            comp: "UNKNOWN" for comp in core_components
        }
        self._alignment_status: Dict[str, str] = {}
        self._action_log: List[Dict[str, Any]] = []

    def _update_health(self, component: str, status: str):
        self._component_health[component] = status

    def _assess_alignment(self):
        healthy_count = sum(
            1 for status in self._component_health.values() if status == "HEALTHY"
        )
        total_count = len(self._component_health)

        if healthy_count == total_count:
            self._alignment_status["overall"] = "PERFECT_HARMONY"
        elif healthy_count >= total_count * 0.7:
            self._alignment_status["overall"] = "MINOR_MISALIGNMENT"
        else:
            self._alignment_status["overall"] = "CRITICAL_DISRUPTION"

        self._alignment_status["details"] = {
            k: v for k, v in self._component_health.items() if v != "HEALTHY"
        }

    def _trigger_remediation(self):
        if self._alignment_status.get("overall") == "CRITICAL_DISRUPTION":
            print(
                f"[ALIGNMENT ENGINE ACTION] CRITICAL: Initiating emergency reconciliation!"
            )
            self._action_log.append(
                {
                    "timestamp": time.time(),
                    "action": "EMERGENCY_RECONCILE",
                    "details": self._alignment_status["details"],
                }
            )
        elif self._alignment_status.get("overall") == "MINOR_MISALIGNMENT":
            print(
                f"[ALIGNMENT ENGINE ACTION] WARNING: Attempting graceful realignment."
            )
            self._action_log.append(
                {
                    "timestamp": time.time(),
                    "action": "GRACEFUL_REALIGN",
                    "details": self._alignment_status["details"],
                }
            )

    def orchestrate_cycle(self):
        self._assess_alignment()
        print(f"\n--- Orchestration Cycle at {time.time():.2f} ---")
        print(f"  Overall Alignment: {self._alignment_status['overall']}")
        if self._alignment_status["details"]:
            print(f"  Issues: {self._alignment_status['details']}")
        self._trigger_remediation()

    def receive_component_pulse(self, component_name: str, health_status: str):
        self._update_health(component_name, health_status)
        print(f"  Received pulse from {component_name}: {health_status}")


if __name__ == "__main__":
    components = ["FeatureStore", "InferenceAPI", "ModelRegistry", "DataPipeline"]
    engine = CelestialAlignmentEngine(components)

    print("--- Simulating Celestial Alignment ---")

    # Initial state (UNKNOWN)
    engine.orchestrate_cycle()

    # Some components become healthy
    engine.receive_component_pulse("FeatureStore", "HEALTHY")
    engine.receive_component_pulse("InferenceAPI", "HEALTHY")
    engine.orchestrate_cycle()

    # One component becomes unhealthy
    engine.receive_component_pulse("DataPipeline", "DEGRADED")
    engine.orchestrate_cycle()

    # All healthy
    engine.receive_component_pulse("ModelRegistry", "HEALTHY")
    engine.receive_component_pulse("DataPipeline", "HEALTHY")
    engine.orchestrate_cycle()

    # Critical disruption
    engine.receive_component_pulse("InferenceAPI", "CRITICAL_FAILURE")
    engine.receive_component_pulse("DataPipeline", "DEGRADED")
    engine.orchestrate_cycle()

    print("\n--- Action Log ---")
    for action in engine._action_log:
        print(action)
