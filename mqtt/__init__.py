#mqtt/__init__.py

from .mqtt_client import MQTTClient
from config.mqtt_config import MQTTConfig

# Create a single instance of the MQTT client
mqtt = MQTTClient(
    broker_host=MQTTConfig.BROKER_HOST,
    broker_port=MQTTConfig.BROKER_PORT,
    client_id=MQTTConfig.CLIENT_ID
)

# Connect to the broker
mqtt.connect()
