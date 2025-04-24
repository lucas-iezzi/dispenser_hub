import json
import time
import asyncio
from mqtt import MQTTClient
from config import MQTTConfig
from utils.enums import Node, Status
from config.topics import MANAGER_TOPIC, KIOSK_TOPIC

#Initialize MQTT Broker
mqtt = MQTTClient(
    broker_host=MQTTConfig.BROKER_HOST,
    broker_port=MQTTConfig.BROKER_PORT,
    client_id="MQTTTestMQTTClient"
)
mqtt.connect()

async def main():

    def handle_message(topic, payload):
        print(f"Received on topic '{topic}': {payload}")

    mqtt.subscribe(MANAGER_TOPIC, handle_message)

    # Keep the script running
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
