import json
import time
import threading
from pathlib import Path
from mqtt_client import get_mqtt_client
from utils import MachineCommand, StatusEnum  # Pydantic model for incoming messages, and standard status options
from config import COMMAND_TOPIC, RESPONSE_TOPIC_BASE, MACHINE_UPDATE_TOPIC_BASE # Imports topic names and formats


# Path to backup machine states in JSON
STATE_FILE = Path("data/machine_states.json")

# Dictionary to hold current machine states in memory
machine_states = {}

# Lock to ensure prevent multiple threads from accessing machine_states at the same time
state_lock = threading.Lock()

def load_machine_states():
    """Load machine states from file into memory on startup or reboot."""
    global machine_states
    if STATE_FILE.exists():
        with STATE_FILE.open("r") as f:
            machine_states = json.load(f)
    else:
        machine_states = {}

def save_machine_states():
    """Save the current machine states to disk (thread-safe)."""
    with state_lock:
        with STATE_FILE.open("w") as f:
            json.dump(machine_states, f, indent=2)

def update_machine_state(machine_id, status_data):
    """Update the in-memory machine state for a given machine (thread-safe)."""
    with state_lock:
        machine_states[machine_id] = status_data

def periodic_save(interval=30):
    """Background thread function that saves machine states periodically."""
    while True:
        time.sleep(interval)
        save_machine_states()

def on_connect(client, userdata, flags, rc):
    """MQTT on_connect callback: subscribes to command topic."""
    print("Connected with result code", rc)
    client.subscribe(COMMAND_TOPIC)

def on_message(client, userdata, msg):
    """MQTT on_message callback: handles incoming messages and routes updates."""
    try:
        # Parse incoming message as a Pydantic object, MachineCommand is defined to be a common message type across nodes
        command = MachineCommand.parse_raw(msg.payload)
        """
        @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        Eventually will need to add handling of machine status here, if the status is being set to active when it is already active for example
        Likely this will either be a duplicate command being send, in which case if it matches the origin and duration and approximately the same timestamp the second command will be ignored
        Possibly this is two commands sent from different nodes, such as activating through the kiosk at the same time as online reservation
        In this case there will have to be handling here to make sure only one status update is sent through to the machine, and the other is rejected back to the orign node instead of acknowledged
        This handling of commands needs to happen before any statuses are updated or updates or responses are sent
        @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        """
        # Convert the command object to a dict to update internal state
        update_machine_state(command.machine_id, command.dict())

        # Publish update to external machine using machine message model
        machine_topic = MACHINE_UPDATE_TOPIC_BASE.format(id=command.machine_id)
        client.publish(machine_topic, command.json())
        
        # Send acknowledgment back to origin node using same message contents
        response_topic = RESPONSE_TOPIC_BASE.format(origin_node=command.origin_node)
        response = {
            "machine_id": command.machine_id,
            "status": command.status,
            "timestamp": command.timestamp,
            "result": "acknowledged"
        }
        client.publish(response_topic, json.dumps(response))

    except Exception as e:
        print("Error handling message:", e)

# Main execution entrypoint
if __name__ == "__main__":
    load_machine_states()  # Load saved machine states

    # Start background thread for periodic JSON saving
    threading.Thread(target=periodic_save, daemon=True).start()

    # Set up MQTT client and callbacks
    client = get_mqtt_client()
    client.on_connect = on_connect
    client.on_message = on_message

    # Connect to MQTT broker and start loop
    client.connect("localhost", 1883, 60)
    client.loop_forever()