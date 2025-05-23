# machine_handler.py

import asyncio
import time
from datetime import datetime
from multiprocessing import Manager, Event
from mqtt import MQTTClient
from config import MQTTConfig
from config import (
    HANDLER_TOPIC_INTERNAL,
    machine_topic,
    TOPIC_MAP
)
from utils import MACHINE, CONFIRMATION
from utils import get_logger
from utils import Node
from nodes import load_master_schedule, save_master_schedule

#Initialize MQTT Broker
mqtt = MQTTClient(
    broker_host=MQTTConfig.BROKER_HOST,
    broker_port=MQTTConfig.BROKER_PORT,
    client_id="MachineHandlerMQTTClient"
)
mqtt.connect()

# Define the current node
selfNode = Node.HANDLER

# Initialize the logger
logger = get_logger("MachineHandler")

# Shared dictionary for today_schedule
manager = Manager()
master_schedule = manager.dict()

# Initialize the master schedule update flag
master_schedule_flag = Event()

# Active time bucket tracking
active_time_bucket_index = -1
previous_time_bucket_index = -1

def main(shared_state, shared_state_flag, ready_event, loop):
    """
    Entry point for the machine_handler node. Sets up MQTT subscriptions and starts the event loop.
    """
    global master_schedule_flag  # Flag used to tell machine_handler when the master schedule has been updated
    master_schedule_flag = shared_state_flag
    global master_schedule
    master_schedule = shared_state  # Use the shared state

    # Wait for the schedule_manager to signal readiness
    logger.info("Waiting for Schedule Manager to be ready...")
    ready_event.wait()
    logger.info("Starting Machine Handler.")
    
    # Check if today's schedule exists in the shared variable
    current_date = datetime.now().strftime("%Y-%m-%d")
    if current_date not in master_schedule:
        logger.info(f"Today's schedule not found in shared state. Attempting to load from file.")
        # Attempt to load the schedule from file
        schedule = load_master_schedule(current_date)
        master_schedule[current_date] = schedule
        save_master_schedule(schedule, current_date)  # Save the schedule to ensure it exists on disk
    else:
        logger.info(f"Today's schedule already exists in shared state. Skipping file load.")

    # Subscribe to the internal handler topic for machine updates and requests
    mqtt.subscribe(HANDLER_TOPIC_INTERNAL, incoming_message_processor_internal)

    # Add tasks to the shared event loop
    loop.create_task(run_event_loop())
    logger.info("Schedule Manager tasks added to the event loop.")
    
async def run_event_loop():
    asyncio.create_task(monitor_active_time_bucket())
    # asyncio.create_task(monitor_master_schedule())
    logger.info("Machine handler started and subscribed to topics.")
    
    # Keep the event loop alive forever
    await asyncio.Event().wait()

# async def monitor_master_schedule():
    # wait for the master_schedule_flag to indicate new content is available then check against previous content to see what machines to update
    # may need to change active_time_bucket_index to store the whole active time bucket instead

async def monitor_active_time_bucket():
    """
    Periodically check the current time and determine the active time bucket.
    Send MACHINE status change requests for machines whose statuses have changed.
    """
    global master_schedule, active_time_bucket_index, previous_time_bucket_index

    while True:
        try:
            # Get the current time and date
            now = time.time()
            current_date = datetime.fromtimestamp(now).strftime("%Y-%m-%d")

            # Check if the current day's schedule exists in the shared dictionary
            if current_date not in master_schedule:
                logger.warning(f"No schedule found for {current_date} in master_schedule.")
                await asyncio.sleep(1)
                continue

            today_schedule = master_schedule[current_date]

            # Determine the active time bucket
            for i, time_bucket in enumerate(today_schedule):
                if time_bucket[0] > now:
                    break
                active_time_bucket_index = i

            # Only compare the active bucket to the previous one if the active bucket has changed
            if active_time_bucket_index != previous_time_bucket_index:
                logger.info(f"Active time bucket updated to index {active_time_bucket_index}.")
                update_active_time_bucket(today_schedule)
                previous_time_bucket_index = active_time_bucket_index

            # Sleep for a short interval before checking again
            await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error in monitor_active_time_bucket: {e}")


def update_active_time_bucket(today_schedule):
    """
    Compare the active time bucket to the previous one chronologically.
    Send MACHINE status change requests for machines whose statuses have changed.
    """
    global active_time_bucket_index, previous_time_bucket_index

    if previous_time_bucket_index == -1:
        # No previous time bucket to compare
        logger.info("No previous time bucket to compare. Setting all machines to the state of the first time bucket.")
        first_time_bucket = today_schedule[0]
        send_machine_updates(first_time_bucket[1:])  # Pass all machines in the first time bucket
        return

    # Get the current and previous time buckets
    current_time_bucket = today_schedule[active_time_bucket_index]
    previous_time_bucket = today_schedule[previous_time_bucket_index]

    # Identify machines whose statuses have changed
    changed_machines = [
        current_machine
        for current_machine, previous_machine in zip(current_time_bucket[1:], previous_time_bucket[1:])
        if current_machine.status != previous_machine.status
    ]

    # Send updates for machines that have changed
    if changed_machines:
        logger.info(f"Found {len(changed_machines)} machines with status changes in the active time bucket.")
        send_machine_updates(changed_machines)


def send_machine_updates(machines):
    """
    Send MACHINE status updates for a list of machines.

    Args:
        machines (List[MACHINE]): The list of MACHINE objects to update.
    """
    for machine in machines:
        try:
            # Generate a unique exchange_id for the machine update
            machine.exchange_id = generate_exchange_id()

            # Publish the machine update to the HANDLER_TOPIC_INTERNAL
            mqtt.publish(HANDLER_TOPIC_INTERNAL, machine.json())
            logger.info(f"Sent status update for machine {machine.machine_id} with exchange ID {machine.exchange_id}")

        except Exception as e:
            logger.error(f"Failed to send status update for machine {machine.machine_id}: {e}")


def generate_exchange_id() -> int:
    """
    Generate a unique exchange ID for machine updates.
    """
    return int(time.time() * 1000)


async def incoming_message_processor_internal(topic: str, message: str):
    """
    Callback for messages received on HANDLER_TOPIC_INTERNAL.
    Handles machine updates and requests for machine information.
    """
    try:
        # Try to parse as Machine
        machine_update = MACHINE.parse_raw(message)
        logger.info(f"Received machine update for ID {machine_update.machine_id}")

        # Update the shared dictionary
        current_date = datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d")
        if current_date in master_schedule:
            today_schedule = master_schedule[current_date]
            for time_bucket in today_schedule:
                for idx, machine in enumerate(time_bucket[1:], start=1):
                    if machine.machine_id == machine_update.machine_id:
                        time_bucket[idx] = machine_update
                        break

            # Update the shared dictionary
            master_schedule[current_date] = today_schedule

        # Forward the machine update
        mqtt.publish(machine_topic(machine_update.machine_id), machine_update.json())
        logger.info(f"Forwarded machine update to {machine_topic(machine_update.machine_id)}")

    except Exception as e:
        logger.error(f"Failed to parse message on {HANDLER_TOPIC_INTERNAL}: {e}")
