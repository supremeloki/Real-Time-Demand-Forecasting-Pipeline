import sys
import os
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, 'src'))

from kafka import KafkaProducer
import json
import logging
from src.utils.config_reader import ConfigReader
from src.utils.logging_setup import setup_logging

logger = setup_logging(__name__)

class SnappKafkaProducer:
    def __init__(self, env: str = "dev"):
        config = ConfigReader(env)
        self.bootstrap_servers = config.get("kafka.bootstrap_servers")
        self.producer = self._create_producer()

    def _create_producer(self):
        try:
            producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=5
            )
            logger.info(f"Kafka producer connected to {self.bootstrap_servers}")
            return producer
        except Exception as e:
            logger.error(f"Failed to connect Kafka producer: {e}")
            raise

    def send_message(self, topic: str, message: dict):
        try:
            future = self.producer.send(topic, message)
            record_metadata = future.get(timeout=10)
            logger.debug(f"Message sent to topic {record_metadata.topic} partition {record_metadata.partition} offset {record_metadata.offset}")
        except Exception as e:
            logger.error(f"Failed to send message to topic {topic}: {e}")

    def flush(self):
        self.producer.flush()

    def close(self):
        self.producer.close()
        logger.info("Kafka producer closed.")