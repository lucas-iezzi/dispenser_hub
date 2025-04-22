import json
import time
from mqtt import mqtt
from utils.enums import Node, Status
from config.topics import HANDLER_TOPIC_INTERNAL

def on_handler_message(client, userdata, message):
    print(f"Received on {message.topic}: {message.payload.decode()}")

def main():
    # Subscribe to HANDLER_TOPIC_INTERNAL to verify the update
    mqtt.subscribe(HANDLER_TOPIC_INTERNAL, on_handler_message)

    # Create a machine status update message
    machine_status = {
        "machine_id": 1,
        "status": Status.ACTIVE.value,
        "last_updated": time.time(),
        "origin_node": Node.HANDLER.value,
        "destination_node": Node.MANAGER.value
    }

    # Publish the machine status update to HANDLER_TOPIC_INTERNAL
    mqtt.publish(HANDLER_TOPIC_INTERNAL, json.dumps(machine_status))
    print(f"Published machine status update to {HANDLER_TOPIC_INTERNAL}")

    # Wait to verify the update
    time.sleep(5)

if __name__ == "__main__":
    main()
