import collections
import time
import random
from typing import Any


class HarmonySynchronizer:
    def __init__(self, key_lifetime_seconds=300):
        self._key_states = collections.defaultdict(dict)
        self._key_timestamps = collections.defaultdict(float)
        self.key_lifetime_seconds = key_lifetime_seconds

    def register_state(self, entity_id: str, component_name: str, state_value: Any):
        self._key_states[entity_id][component_name] = state_value
        self._key_timestamps[entity_id] = time.time()

    def get_harmonized_state(self, entity_id: str):
        if (
            time.time() - self._key_timestamps.get(entity_id, 0)
            > self.key_lifetime_seconds
        ):
            self._key_states.pop(entity_id, None)
            self._key_timestamps.pop(entity_id, None)
            return None
        return self._key_states.get(entity_id)

    def prune_stale_entries(self):
        current_time = time.time()
        stale_entities = [
            entity_id
            for entity_id, timestamp in self._key_timestamps.items()
            if current_time - timestamp > self.key_lifetime_seconds
        ]
        for entity_id in stale_entities:
            self._key_states.pop(entity_id, None)
            self._key_timestamps.pop(entity_id, None)


if __name__ == "__main__":
    synchronizer = HarmonySynchronizer(key_lifetime_seconds=5)

    synchronizer.register_state("user_123", "ProfileService", {"name": "Alice"})
    synchronizer.register_state("user_123", "RecommendationEngine", {"score": 0.9})
    synchronizer.register_state("prod_456", "InventorySystem", {"stock": 100})

    print(f"User 123 state: {synchronizer.get_harmonized_state('user_123')}")
    print(f"Product 456 state: {synchronizer.get_harmonized_state('prod_456')}")

    time.sleep(6)
    synchronizer.prune_stale_entries()
    print(
        f"User 123 state after prune: {synchronizer.get_harmonized_state('user_123')}"
    )
