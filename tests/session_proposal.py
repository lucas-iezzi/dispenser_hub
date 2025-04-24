import json
import time
from mqtt import mqtt
from utils.enums import Node, Status
from config.topics import MANAGER_TOPIC, KIOSK_TOPIC

# Flag to indicate confirmation received
confirmation_received = False

def on_kiosk_message(client, userdata, message):
    global confirmation_received
    print(f"Received on {message.topic}: {message.payload.decode()}")
    confirmation_received = True  # Set the flag when confirmation is received

def main():
    global confirmation_received

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

    # Wait for confirmation
    timeout = 10  # Wait for up to 10 seconds
    start_time = time.time()
    while not confirmation_received and time.time() - start_time < timeout:
        time.sleep(0.5)

    if confirmation_received:
        print("Confirmation received!")
    else:
        print("No confirmation received within the timeout period.")

if __name__ == "__main__":
    main()
