import json
import time
from mqtt import mqtt
from utils.enums import Node, Status
from config.topics import MANAGER_TOPIC, KIOSK_TOPIC

def on_kiosk_message(client, userdata, message):
    print(f"Received on {message.topic}: {message.payload.decode()}")

def main():
    # Subscribe to KIOSK_TOPIC to receive confirmation
    mqtt.subscribe(KIOSK_TOPIC, on_kiosk_message)

    # Create a session proposal message
    session_proposal = {
        "machine_id": [1, 2],
        "session_id": 123,
        "status": Status.RESERVED.value,
        "start_time": time.time() + 60,  # Start in 1 minute
        "duration": 3600,  # 1 hour
        "origin_node": Node.KIOSK.value,
        "destination_node": Node.MANAGER.value
    }

    # Publish the session proposal to MANAGER_TOPIC
    mqtt.publish(MANAGER_TOPIC, json.dumps(session_proposal))
    print(f"Published session proposal to {MANAGER_TOPIC}")

    # Wait to receive confirmation
    time.sleep(5)

if __name__ == "__main__":
    main()
