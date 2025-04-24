import paho.mqtt.client as mqtt
from utils.logger import get_logger
from typing import Callable, Dict

class MQTTClient:
    def __init__(self, broker_host: str, broker_port: int, client_id: str = None):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id or f"mqtt_client_{id(self)}"
        self.client = mqtt.Client(self.client_id)
        self.logger = get_logger(self.client_id)
        self._callbacks: Dict[str, Callable[[str, str], None]] = {}  # topic -> callback

    def connect(self):
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.connect(self.broker_host, self.broker_port)
        self.logger.info(f"Connecting to MQTT broker at {self.broker_host}:{self.broker_port}")
        self.client.loop_start()

    def subscribe(self, topic: str, callback: Callable[[str, str], None]):
        self.client.subscribe(topic)
        self._callbacks[topic] = callback  # Store the callback
        self.logger.info(f"Subscribed to topic: {topic}")

    def publish(self, topic: str, payload: str):
        self.client.publish(topic, payload)
        self.logger.info(f"Published message to topic: {topic}")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logger.info("Connected to MQTT broker successfully.")
        else:
            self.logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self.logger.info("Disconnected from MQTT broker.")

    def _on_message(self, client, userdata, message):
        topic = message.topic
        payload = message.payload.decode()
        self.logger.info(f"Received message on topic {topic}: {payload}")

        callback = self._callbacks.get(topic)
        if callback:
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(topic, payload))
                else:
                    callback(topic, payload)
            except Exception as e:
                self.logger.error(f"Error in callback for topic {topic}: {e}")
        else:
            self.logger.warning(f"No callback registered for topic {topic}")
