# tests/test_propose_session.py

import json
import time

from mqtt import MQTTClient, MQTTConfig
from config import Topics
from utils.messages import SESSION

response_received = False

def handle_response(topic: str, payload: str):
    global response_received
    print(f"\nReceived response on {topic}:\n{payload}")
    response_received = True

# Initialize MQTT client
mqtt_client = MQTTClient(
    broker_host=MQTTConfig.BROKER_HOST,
    broker_port=MQTTConfig.BROKER_PORT,
    client_id="TestProposeSession"
)
mqtt_client.connect()

# Subscribe to response topic
mqtt_client.subscribe(Topics.TEST_SESSION_RESPONSE, handle_response)

# Create a sample session proposal
session = SESSION(
    session_id=12345,
    exchange_id=12345,
    machine_ids=[1, 2],
    start_time=(time.time()),
    duration=3600
)

# Convert to JSON and publish
payload = json.dumps(session)
mqtt_client.publish(Topics.MANAGER_PROPOSE_SESSION, payload)
print(f"Published test session proposal:\n{payload}")

# Wait up to 5 seconds for a response
for _ in range(10):
    if response_received:
        break
    time.sleep(0.5)

if not response_received:
    print("\nNo response received within 5 seconds.")