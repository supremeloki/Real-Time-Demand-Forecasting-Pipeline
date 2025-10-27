from kafka import KafkaConsumer
import json
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PredictionFeedbackConsumer:
    def __init__(self, topic: str, bootstrap_servers: str = 'localhost:9092', group_id: str = 'feedback_group'):
        self.topic = topic
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True
        )
        logging.info(f"Initialized Kafka consumer for topic: {topic}")

    def consume_feedback(self):
        logging.info("Starting to consume prediction feedback...")
        try:
            for message in self.consumer:
                feedback_data = message.value
                logging.info(f"Received feedback: {feedback_data}")
                # Here, you would typically process the feedback:
                # - Store it in a database for monitoring
                # - Calculate real-time prediction error
                # - Update model performance metrics
                self.process_feedback(feedback_data)
        except KeyboardInterrupt:
            logging.info("Stopping feedback consumer.")
        finally:
            self.consumer.close()

    def process_feedback(self, data: dict):
        # Example processing: log key fields
        predicted_demand = data.get('predicted_demand')
        actual_rides = data.get('actual_rides')
        geohash = data.get('geohash_id')
        timestamp = data.get('timestamp')
        logging.debug(f"Processed feedback for geohash {geohash} at {timestamp}: Predicted={predicted_demand}, Actual={actual_rides}")
        # Add actual error calculation and storage logic here

if __name__ == '__main__':
    # Ensure Kafka is running (e.g., via docker-compose from 03_SNAPPTECH_DEMO_GUIDE.md)
    feedback_topic = "snapp.demand_prediction_feedback"
    consumer = PredictionFeedbackConsumer(feedback_topic)
    consumer.consume_feedback()