import json
import time
from mqtt import mqtt
from utils.enums import Node, Request
from config.topics import MANAGER_TOPIC, KIOSK_TOPIC

def on_kiosk_message(client, userdata, message):
    print(f"Received on {message.topic}: {message.payload.decode()}")

def main():

    # Subscribe to KIOSK_TOPIC to receive the schedule
    mqtt.subscribe(KIOSK_TOPIC, on_kiosk_message)

    # Create a schedule request message
    schedule_request = {
        "request_type": Request.SCHEDULE.value,
        "timestamp": time.time(),
        "origin_node": Node.KIOSK.value,
        "destination_node": Node.MANAGER.value
    }

    # Publish the schedule request to MANAGER_TOPIC
    mqtt.publish(MANAGER_TOPIC, json.dumps(schedule_request))
    print(f"Published schedule request to {MANAGER_TOPIC}")

    # Wait to receive the schedule
    time.sleep(5)

if __name__ == "__main__":
    main()
