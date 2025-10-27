import collections
import time
import json

class EphemeralInsightEngine:
    def __init__(self, observation_window_seconds=10, trigger_threshold=5):
        self._event_buffer = collections.deque()
        self.observation_window_seconds = observation_window_seconds
        self.trigger_threshold = trigger_threshold

    def ingest_pulse(self, pulse: dict):
        current_time = time.time()
        self._event_buffer.append((current_time, pulse))

        while self._event_buffer and self._event_buffer[0][0] < current_time - self.observation_window_seconds:
            self._event_buffer.popleft()

    def generate_flash_insight(self):
        insight_count = len(self._event_buffer)
        if insight_count >= self.trigger_threshold:
            return {"insight_level": "CRITICAL", "pulse_count": insight_count, "window_start": self._event_buffer[0][0] if self._event_buffer else None, "window_end": time.time()}
        return {"insight_level": "NORMAL", "pulse_count": insight_count}

if __name__ == '__main__':
    engine = EphemeralInsightEngine(observation_window_seconds=3, trigger_threshold=4)

    for i in range(10):
        engine.ingest_pulse({"type": "request", "id": i})
        insight = engine.generate_flash_insight()
        print(f"Time {time.time():.2f}: {insight}")
        time.sleep(0.5)

    print(f"\nFinal insight after cooldown: {engine.generate_flash_insight()}")