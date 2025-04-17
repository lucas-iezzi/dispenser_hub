import os

class MQTTConfig:
    """
    Configuration for the MQTT client.
    """

    # Default to the static IP of the Raspberry Pi's Ethernet port
    BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "192.168.4.1")
    BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", 1883))  # Default to port 1883
    CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "default_client")  # Default client ID
