import sys
import os
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, 'src'))

from kafka import KafkaConsumer
import json
import logging
from src.utils.config_reader import ConfigReader
from src.utils.logging_setup import setup_logging

logger = setup_logging(__name__)

class SnappKafkaConsumer:
    def __init__(self, topic: str, group_id: str, env: str = "dev"):
        config = ConfigReader(env)
        self.bootstrap_servers = config.get("kafka.bootstrap_servers")
        self.topic = topic
        self.group_id = group_id
        self.consumer = self._create_consumer()

    def _create_consumer(self):
        try:
            consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest', # Start from beginning if no offset committed
                enable_auto_commit=True,
                auto_commit_interval_ms=5000 # Commit every 5 seconds
            )
            logger.info(f"Kafka consumer for topic {self.topic} (group: {self.group_id}) connected to {self.bootstrap_servers}")
            return consumer
        except Exception as e:
            logger.error(f"Failed to connect Kafka consumer: {e}")
            raise

    def poll_messages(self, timeout_ms: int = 1000, max_records: int = None):
        messages = self.consumer.poll(timeout_ms=timeout_ms, max_records=max_records)
        parsed_messages = []
        for tp, records in messages.items():
            for record in records:
                parsed_messages.append(record.value)
        return parsed_messages

    def close(self):
        self.consumer.close()
        logger.info("Kafka consumer closed.")