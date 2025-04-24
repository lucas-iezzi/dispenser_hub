import paho.mqtt.client as mqtt
from utils.logger import get_logger

class MQTTClient:
    """
    A wrapper around the paho-mqtt client to handle MQTT communication.
    """

    def __init__(self, broker_host: str, broker_port: int, client_id: str = None):
        """
        Initialize the MQTT client.

        Args:
            broker_host (str): The hostname or IP address of the MQTT broker.
            broker_port (int): The port number of the MQTT broker.
            client_id (str, optional): A unique client ID. Defaults to None.
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id or f"mqtt_client_{id(self)}"
        self.client = mqtt.Client(self.client_id)
        self.logger = get_logger(f"{client_id}")  # Use the common logger utility

    def connect(self):
        """
        Connect to the MQTT broker.
        """
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.connect(self.broker_host, self.broker_port)
        self.logger.info(f"Connecting to MQTT broker at {self.broker_host}:{self.broker_port}")
        self.client.loop_start()

    def subscribe(self, topic: str, callback):
        """
        Subscribe to a topic.

        Args:
            topic (str): The MQTT topic to subscribe to.
            callback (function): The callback function to handle incoming messages.
        """
        self.client.subscribe(topic)
        self.client.message_callback_add(topic, callback)
        self.logger.info(f"Subscribed to topic: {topic}")

    def publish(self, topic: str, payload: str):
        """
        Publish a message to a topic.

        Args:
            topic (str): The MQTT topic to publish to.
            payload (str): The message payload.
        """
        self.client.publish(topic, payload)
        self.logger.info(f"Published message to topic: {topic}")

    def _on_connect(self, client, userdata, flags, rc):
        """
        Callback for when the client connects to the broker.
        """
        if rc == 0:
            self.logger.info("Connected to MQTT broker successfully.")
        else:
            self.logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """
        Callback for when the client disconnects from the broker.
        """
        self.logger.info("Disconnected from MQTT broker.")

    def _on_message(self, client, userdata, message):
        """
        Callback for when a message is received on a subscribed topic.
        """
        self.logger.info(f"Received message on topic {message.topic}: {message.payload.decode()}")
