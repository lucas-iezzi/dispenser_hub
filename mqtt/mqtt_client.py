import asyncio
import paho.mqtt.client as mqtt
from utils.logger import get_logger
from typing import Callable, Dict, Optional

class MQTTClient:
    def __init__(self, broker_host: str, broker_port: int, client_id: str):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id
        self.client = mqtt.Client(self.client_id)
        self.logger = get_logger(self.client_id)
        self._callbacks: Dict[str, Callable[[str, str], None]] = {}
        self._loop = asyncio.get_event_loop()

    def connect(self):
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        self.logger.info(f"Connecting to MQTT broker at {self.broker_host}:{self.broker_port}...")
        self.client.connect(self.broker_host, self.broker_port)
        self.client.loop_start()

    def subscribe(self, topic: str, callback: Callable[[str, str], None]):
        """Subscribe and register a callback for a specific topic."""
        self.client.subscribe(topic)
        self._callbacks[topic] = callback
        self.logger.info(f"Subscribed to topic: {topic}")

    def publish(self, topic: str, payload: str):
        """Publish a message to a topic."""
        self.client.publish(topic, payload)
        self.logger.info(f"Published message to topic {topic}: {payload}")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logger.info("MQTT connected successfully.")
        else:
            self.logger.error(f"MQTT connection failed. Return code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self.logger.info("MQTT disconnected.")

    def _on_message(self, client, userdata, message):
        topic = message.topic
        payload = message.payload.decode()

        self.logger.info(f"Received message on topic {topic}: {payload}")

        callback = self._callbacks.get(topic)
        if callback:
            try:
                if asyncio.iscoroutinefunction(callback):
                    # Run async callback in the event loop
                    self._loop.call_soon_threadsafe(asyncio.create_task, callback(topic, payload))
                else:
                    # Run sync callback immediately
                    callback(topic, payload)
            except Exception as e:
                self.logger.exception(f"Error in MQTT callback for topic '{topic}': {e}")
        else:
            self.logger.warning(f"No callback registered for topic: {topic}")
