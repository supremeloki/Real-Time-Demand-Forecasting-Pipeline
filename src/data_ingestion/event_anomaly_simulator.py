import logging
import json
from datetime import datetime, timedelta
import random
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EventAnomalySimulator:
    """
    Generates synthetic ride events and can inject specific types of anomalies
    (e.g., sudden spikes, drops, or corrupted data) into the stream.
    Useful for testing monitoring and anomaly detection systems.
    """
    def __init__(self, kafka_producer=None, input_topic: str = "snapp.ride_events_raw",
                 geohash_pool: List[str] | None = None):
        self.kafka_producer = kafka_producer # Expects an instance of SnappKafkaProducer
        self.input_topic = input_topic
        self.geohash_pool = geohash_pool if geohash_pool else ["dr5ru", "dr5ry", "dr5rz", "dr5r7", "dr5rg"]
        self.normal_base_request_count = 10
        
        logging.info("EventAnomalySimulator initialized.")

    def _generate_normal_event(self, geohash_id: str, timestamp: datetime) -> Dict[str, Any]:
        """Generates a single, normal ride event."""
        request_count = max(1, round(random.gauss(self.normal_base_request_count, 3)))
        return {
            "geohash_id": geohash_id,
            "timestamp": timestamp.isoformat() + "Z", # ISO 8601 with Z for UTC
            "request_count": request_count,
            "event_type": "normal_ride_request"
        }

    def _generate_spike_anomaly_event(self, geohash_id: str, timestamp: datetime, spike_factor: float = 5.0) -> Dict[str, Any]:
        """Generates a ride event with a sudden spike in requests."""
        request_count = max(self.normal_base_request_count * spike_factor, round(random.gauss(self.normal_base_request_count * spike_factor, 10)))
        logging.warning(f"Injecting spike anomaly in {geohash_id} at {timestamp}: {request_count} requests.")
        return {
            "geohash_id": geohash_id,
            "timestamp": timestamp.isoformat() + "Z",
            "request_count": int(request_count),
            "event_type": "spike_anomaly"
        }

    def _generate_drop_anomaly_event(self, geohash_id: str, timestamp: datetime, drop_factor: float = 0.1) -> Dict[str, Any]:
        """Generates a ride event with a sudden drop in requests (near zero)."""
        request_count = max(0, round(random.gauss(self.normal_base_request_count * drop_factor, 1)))
        logging.warning(f"Injecting drop anomaly in {geohash_id} at {timestamp}: {request_count} requests.")
        return {
            "geohash_id": geohash_id,
            "timestamp": timestamp.isoformat() + "Z",
            "request_count": int(request_count),
            "event_type": "drop_anomaly"
        }
        
    def _generate_corrupted_event(self, geohash_id: str, timestamp: datetime) -> Dict[str, Any]:
        """Generates a data event with an invalid type or missing required field."""
        corrupted_event = {
            "geohash_id": geohash_id,
            "timestamp": timestamp.isoformat() + "Z",
            "request_count": "invalid_count", # Corrupted type
            "event_type": "corrupted_data_anomaly"
        }
        if random.random() < 0.5: # Also sometimes miss a field
            del corrupted_event["geohash_id"]
        logging.warning(f"Injecting corrupted data anomaly: {corrupted_event}")
        return corrupted_event

    def simulate_events(self, num_events: int = 100, anomaly_freq: float = 0.05,
                        anomaly_type: str = "random"):
        """
        Simulates a stream of events, with a chance to inject anomalies.
        """
        logging.info(f"Starting event simulation for {num_events} events. Anomaly frequency: {anomaly_freq}")
        current_time = datetime.now()

        for i in range(num_events):
            geohash = random.choice(self.geohash_pool)
            event_time = current_time + timedelta(seconds=i * random.uniform(5, 15)) # Events spread out

            event_data = {}
            if random.random() < anomaly_freq:
                chosen_anomaly = anomaly_type
                if anomaly_type == "random":
                    chosen_anomaly = random.choice(["spike", "drop", "corrupted"])

                if chosen_anomaly == "spike":
                    event_data = self._generate_spike_anomaly_event(geohash, event_time)
                elif chosen_anomaly == "drop":
                    event_data = self._generate_drop_anomaly_event(geohash, event_time)
                elif chosen_anomaly == "corrupted":
                    event_data = self._generate_corrupted_event(geohash, event_time)
            else:
                event_data = self._generate_normal_event(geohash, event_time)
            
            if self.kafka_producer:
                try:
                    self.kafka_producer.send_message(self.input_topic, event_data)
                    logging.debug(f"Sent event to Kafka: {event_data['event_type']} for {geohash}")
                except Exception as e:
                    logging.error(f"Failed to send event to Kafka: {e}")
            else:
                logging.debug(f"Simulated event (no Kafka): {json.dumps(event_data)}")
            
            # time.sleep(0.01) # Small delay to simulate real-time

        if self.kafka_producer:
            self.kafka_producer.flush()
            logging.info("All simulated events flushed to Kafka.")
        logging.info("Event simulation finished.")

if __name__ == '__main__':
    # Mock Kafka Producer
    class MockKafkaProducer:
        def __init__(self):
            logging.info("MockKafkaProducer initialized.")
            self.sent_messages = []
        def send_message(self, topic, message):
            self.sent_messages.append({"topic": topic, "message": message})
            # logging.info(f"Mocking send to {topic}: {message['event_type']}")
        def flush(self):
            logging.info(f"MockKafkaProducer flushed {len(self.sent_messages)} messages.")
        def close(self):
            logging.info("MockKafkaProducer closed.")

    mock_producer = MockKafkaProducer()
    simulator = EventAnomalySimulator(kafka_producer=mock_producer)

    print("--- Simulating Normal Event Stream ---")
    simulator.simulate_events(num_events=50, anomaly_freq=0)

    print("\n--- Simulating Event Stream with Spike Anomalies ---")
    simulator.simulate_events(num_events=30, anomaly_freq=0.2, anomaly_type="spike")

    print("\n--- Simulating Event Stream with Drop Anomalies ---")
    simulator.simulate_events(num_events=30, anomaly_freq=0.2, anomaly_type="drop")
    
    print("\n--- Simulating Event Stream with Corrupted Anomalies ---")
    simulator.simulate_events(num_events=30, anomaly_freq=0.3, anomaly_type="corrupted")

    print("\nTotal mock messages sent:", len(mock_producer.sent_messages))
    # print("Sample message:", mock_producer.sent_messages[0])