import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DynamicResourceGuardian:
    """
    Simulates a cloud resource autoscaler that monitors application load/metrics
    and makes decisions to scale resources up or down to optimize cost and performance.
    """
    def __init__(self,
                 min_instances: int = 2,
                 max_instances: int = 10,
                 target_cpu_utilization: float = 0.6, # 60%
                 target_qps_per_instance: float = 100.0, # Queries per second
                 scale_up_factor: float = 1.2, # Scale up by 20%
                 scale_down_factor: float = 0.8, # Scale down to 80%
                 cooldown_period_minutes: int = 5):
        
        self.min_instances = min_instances
        self.max_instances = max_instances
        self.target_cpu_utilization = target_cpu_utilization
        self.target_qps_per_instance = target_qps_per_instance
        self.scale_up_factor = scale_up_factor
        self.scale_down_factor = scale_down_factor
        self.cooldown_period = timedelta(minutes=cooldown_period_minutes)
        self.last_scale_action: datetime = datetime.min
        
        self.current_instances = min_instances
        
        logging.info(f"DynamicResourceGuardian initialized. Min={min_instances}, Max={max_instances} instances.")

    def _get_current_metrics(self) -> Dict[str, Any]:
        """
        Simulates fetching real-time metrics (CPU, QPS) from cloud monitoring.
        """
        simulated_cpu_util = random.uniform(0.3, 0.9) # Between 30% and 90%
        simulated_qps = self.current_instances * random.uniform(50, 150) # QPS varies per instance
        
        # Introduce some spikes/drops for dynamic scaling
        if random.random() < 0.1: # 10% chance of a surge
            simulated_cpu_util = random.uniform(0.85, 0.99)
            simulated_qps *= random.uniform(1.5, 2.5)
        elif random.random() < 0.1: # 10% chance of a lull
            simulated_cpu_util = random.uniform(0.1, 0.3)
            simulated_qps *= random.uniform(0.1, 0.5)

        logging.debug(f"Current Metrics: CPU={simulated_cpu_util:.2f}, QPS={simulated_qps:.0f}")
        return {"cpu_utilization": simulated_cpu_util, "queries_per_second": simulated_qps}

    def _calculate_target_instances(self, metrics: Dict[str, Any]) -> int:
        """
        Calculates the desired number of instances based on metrics and targets.
        """
        target_by_cpu = int(self.current_instances * (metrics["cpu_utilization"] / self.target_cpu_utilization))
        target_by_qps = int(metrics["queries_per_second"] / self.target_qps_per_instance)
        
        # Take the maximum of the two targets to avoid under-provisioning
        desired_instances = max(target_by_cpu, target_by_qps)
        
        # Apply scaling factors for hysteresis
        if desired_instances > self.current_instances: # Scale up
            desired_instances = int(self.current_instances * self.scale_up_factor) + 1
        elif desired_instances < self.current_instances: # Scale down
            desired_instances = int(self.current_instances * self.scale_down_factor) 
        
        # Ensure within min/max bounds
        desired_instances = max(self.min_instances, min(self.max_instances, desired_instances))
        
        return desired_instances

    def manage_resources(self) -> Dict[str, Any]:
        """
        Performs a resource management cycle: fetches metrics, calculates target, and scales if needed.
        """
        current_time = datetime.now()
        if (current_time - self.last_scale_action) < self.cooldown_period:
            logging.info(f"Cooldown period active. Skipping scaling for {current_time - self.last_scale_action} (Remaining: {self.cooldown_period - (current_time - self.last_scale_action)})")
            return {"action": "NO_ACTION", "current_instances": self.current_instances, "reason": "Cooldown"}

        metrics = self._get_current_metrics()
        desired_instances = self._calculate_target_instances(metrics)

        action = "NO_ACTION"
        reason = "Metrics within acceptable range"

        if desired_instances > self.current_instances:
            action = "SCALE_UP"
            reason = f"Increased load (CPU: {metrics['cpu_utilization']:.2f}, QPS: {metrics['queries_per_second']:.0f})"
            logging.warning(f"Scaling up from {self.current_instances} to {desired_instances} instances. Reason: {reason}")
            self.current_instances = desired_instances
            self.last_scale_action = current_time
        elif desired_instances < self.current_instances:
            action = "SCALE_DOWN"
            reason = f"Reduced load (CPU: {metrics['cpu_utilization']:.2f}, QPS: {metrics['queries_per_second']:.0f})"
            logging.warning(f"Scaling down from {self.current_instances} to {desired_instances} instances. Reason: {reason}")
            self.current_instances = desired_instances
            self.last_scale_action = current_time
        else:
            logging.info(f"Current instances {self.current_instances} is optimal. Reason: {reason}")

        return {
            "timestamp": current_time.isoformat(),
            "action": action,
            "current_instances": self.current_instances,
            "desired_instances": desired_instances,
            "metrics": metrics,
            "reason": reason
        }

if __name__ == '__main__':
    guardian = DynamicResourceGuardian(min_instances=2, max_instances=10, cooldown_period_minutes=1)

    print("--- Simulating Dynamic Cloud Resource Management ---")
    for i in range(15): # Simulate 15 monitoring cycles
        print(f"\n--- Cycle {i+1} ---")
        status = guardian.manage_resources()
        print(f"  Action: {status['action']}, Instances: {status['current_instances']} (Desired: {status['desired_instances']})")
        print(f"  Reason: {status['reason']}")
        print(f"  CPU Util: {status['metrics']['cpu_utilization']:.2f}, QPS: {status['metrics']['queries_per_second']:.0f}")
        import time
        time.sleep(1) # Simulate monitoring interval