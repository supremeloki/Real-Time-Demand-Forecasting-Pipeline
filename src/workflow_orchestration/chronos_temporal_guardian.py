import time
import datetime
import random
import threading
from typing import Callable

class ChronosTemporalGuardian:
    def __init__(self, monitoring_interval_seconds=10):
        self._scheduled_tasks = {}
        self._last_check_times = {}
        self.monitoring_interval_seconds = monitoring_interval_seconds
        self._lock = threading.Lock()

    def schedule_task(self, task_id: str, interval_seconds: int, callback_func: Callable, initial_delay_seconds: int = 0):
        with self._lock:
            self._scheduled_tasks[task_id] = {
                "interval": interval_seconds,
                "callback": callback_func,
                "next_run_time": time.time() + initial_delay_seconds
            }
            self._last_check_times[task_id] = time.time()
            print(f"Task '{task_id}' scheduled. Next run at {datetime.datetime.fromtimestamp(self._scheduled_tasks[task_id]['next_run_time'])}")

    def cancel_task(self, task_id: str):
        with self._lock:
            if task_id in self._scheduled_tasks:
                del self._scheduled_tasks[task_id]
                self._last_check_times.pop(task_id, None)
                print(f"Task '{task_id}' cancelled.")

    def _monitor_and_execute(self):
        while True:
            time.sleep(self.monitoring_interval_seconds)
            current_time = time.time()
            with self._lock:
                for task_id, task_info in list(self._scheduled_tasks.items()):
                    if current_time >= task_info["next_run_time"]:
                        print(f"Executing task '{task_id}' at {datetime.datetime.fromtimestamp(current_time)}")
                        try:
                            task_info["callback"](task_id)
                        except Exception as e:
                            print(f"Error executing task '{task_id}': {e}")
                        task_info["next_run_time"] = current_time + task_info["interval"]
                    self._last_check_times[task_id] = current_time

    def start_guardian(self):
        monitor_thread = threading.Thread(target=self._monitor_and_execute, daemon=True)
        monitor_thread.start()
        print("Chronos Temporal Guardian started monitoring.")

if __name__ == '__main__':
    guardian = ChronosTemporalGuardian(monitoring_interval_seconds=1)

    def simple_report_task(task_id):
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Task {task_id}: Generating report...")

    def health_check_task(task_id):
        status = "OK" if random.random() > 0.1 else "DEGRADED"
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Task {task_id}: Health check status: {status}")

    guardian.schedule_task("daily_report", 5, simple_report_task, initial_delay_seconds=2)
    guardian.schedule_task("service_health", 3, health_check_task, initial_delay_seconds=1)

    guardian.start_guardian()

    try:
        while True:
            time.sleep(10)
            if random.random() < 0.2:
                if "daily_report" in guardian._scheduled_tasks:
                    print("\nSimulating cancelling daily_report task...")
                    guardian.cancel_task("daily_report")
                else:
                    print("\nSimulating rescheduling daily_report task...")
                    guardian.schedule_task("daily_report", 5, simple_report_task, initial_delay_seconds=2)
            
    except KeyboardInterrupt:
        print("Guardian stopped by user.")