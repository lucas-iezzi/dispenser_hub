# schedule_manager.py

from http.client import CONFLICT
import json
import os
import asyncio
import time
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from multiprocessing import Manager
from mqtt import MQTTClient
from config import MQTTConfig
from config import MANAGER_TOPIC, KIOSK_TOPIC, ADMIN_TOPIC, RESERVATION_TOPIC, TOPIC_MAP
from config import machine_id_list
from utils import SESSION, SCHEDULE, CONFIRMATION, REQUEST, MACHINE
from utils import get_logger
from utils import Status, Node, Request

#Initialize MQTT Broker
mqtt = MQTTClient(
    broker_host=MQTTConfig.BROKER_HOST,
    broker_port=MQTTConfig.BROKER_PORT,
    client_id="ScheduleManagerMQTTClient"
)
mqtt.connect()

# Define the current node
selfNode = Node.MANAGER

# Initialize the logger
logger = get_logger("ScheduleManager")

# Shared dictionary for today_schedule
manager = Manager()
master_schedule = manager.dict()

# Initialize the master schedule update flag
master_schedule_flag = Event()

# Master list of all future sessions
master_session_list = []

# Define time bucket size in seconds (default: 5 minutes = 300 seconds)
TIME_BUCKET_SIZE = 300

def main(shared_state, shared_state_flag, ready_event, loop):
    """
    Entry point for the schedule_manager node. Sets up MQTT subscriptions and starts the event loop.
    """
    global master_schedule_flag  # Flag used to tell machine_handler when the master schedule has been updated
    master_schedule_flag = shared_state_flag
    global master_schedule
    master_schedule = shared_state  # Use the shared state

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

    # Subscribe to the internal manager topic for session proposals and requests
    mqtt.subscribe(MANAGER_TOPIC, incoming_message_processor)

    # Signal that the schedule_manager is ready
    ready_event.set()
    logger.info("Schedule Manager is ready.")

    # Add tasks to the shared event loop
    loop.create_task(run_event_loop())
    logger.info("Schedule Manager tasks added to the event loop.")

async def run_event_loop():
    """
    Run the asyncio event loop and schedule tasks.
    """
    logger.info("Schedule Manager started and subscribed to topics.")

    # Keep the event loop running
    while True:
        await asyncio.sleep(1)



################################################################################################################
################################################################################################################
'''File Caching Functions'''
#--------------------------------------------------------------------------------------------------------------#


def load_master_schedule(date: str) -> list:
    """
    Load the master schedule for a specific date from a JSON file in the schedules directory.
    """
    # Construct the full file path
    schedules_dir = "schedules"
    filename = os.path.join(schedules_dir, f"{date}_schedule.json")

    if os.path.exists(filename):
        try:
            with open(filename, "r") as file:
                # Load the raw JSON data
                raw_schedule = json.load(file)
                schedule = []
                for time_bucket in raw_schedule:
                    timestamp = time_bucket[0]
                    machines = [MACHINE(**m) if isinstance(m, dict) else m for m in time_bucket[1:]]
                    schedule.append([timestamp] + machines)
                logger.info(f"Master schedule for {date} loaded successfully from {filename}.")
                return schedule
        except Exception as e:
            logger.error(f"Failed to load master schedule for {date} from {filename}: {e}")
            raise
    else:
        logger.warning(f"Master schedule for {date} not found in {filename}. Generating a blank schedule.")
        # Generate a blank schedule if the file does not exist
        return generate_blank_schedule(date)

def save_master_schedule(schedule: list, date: str) -> bool:
    """
    Save the master schedule to a JSON file in the schedules directory.
    """
    # Ensure the schedules directory exists
    schedules_dir = "schedules"
    os.makedirs(schedules_dir, exist_ok=True)

    # Construct the full file path
    filename = os.path.join(schedules_dir, f"{date}_schedule.json")

    try:
        with open(filename, "w") as file:
            # Convert MACHINE objects to dictionaries for JSON storage
            raw_schedule = []
            for time_bucket in schedule:
                timestamp = time_bucket[0]
                machines = [m.dict() if isinstance(m, MACHINE) else m for m in time_bucket[1:]]
                raw_schedule.append([timestamp] + machines)
            # Save the JSON data
            json.dump(raw_schedule, file, indent=4)  # Use indent=4 for readability

        logger.info(f"Master schedule for {date} saved successfully to {filename}.")
        return True
    except Exception as e:
        logger.error(f"Failed to save master schedule for {date} to {filename}: {e}")
        return False

def load_master_session_list() -> List[SESSION]:
    """
    Load the master session list from a JSON file and convert it to a list of SESSION models.
    """
    filename = "master_session_list.json"
    if os.path.exists(filename):
        try:
            with open(filename, "r") as file:
                raw_session_list = json.load(file)
                # Convert each dictionary in the JSON list to a SESSION model
                session_list = [SESSION.parse_obj(session) for session in raw_session_list]
                logger.info("Master session list loaded successfully.")
                return session_list
        except Exception as e:
            logger.error(f"Failed to load master session list: {e}")
            return []
    else:
        logger.warning("Master session list file not found. Returning an empty list.")
        return []


def save_master_session_list(session_list: List[SESSION]) -> bool:
    """
    Save the master session list to a JSON file after converting it to a list of dictionaries.
    """
    filename = "master_session_list.json"
    try:
        with open(filename, "w") as file:
            # Convert each SESSION model to a dictionary for JSON storage
            raw_session_list = [session.dict() for session in session_list]
            json.dump(raw_session_list, file)
        logger.info("Master session list saved successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to save master session list: {e}")
        return False



################################################################################################################
################################################################################################################
'''Schedule Managing Helper Functions'''
#--------------------------------------------------------------------------------------------------------------#


def generate_blank_schedule(date: str) -> list:
    """
    Generate a blank schedule for a given day with configurable time bucket intervals.
    """
    # Parse the date string into a datetime object
    start_of_day = datetime.strptime(date, "%Y-%m-%d")

    # Calculate the number of intervals in a day
    intervals_per_day = (24 * 60 * 60) // TIME_BUCKET_SIZE  # Total seconds in a day divided by bucket size

    # Generate timestamps for each interval
    schedule = []
    for i in range(intervals_per_day):
        time_bucket = [int((start_of_day + timedelta(seconds=TIME_BUCKET_SIZE * i)).timestamp())]

        # Add a MACHINE object for each machine ID
        for machine_id in machine_id_list:
            machine = MACHINE(
                machine_id=machine_id,
                status=Status.AVAILABLE,
            )
            time_bucket.append(machine)

        schedule.append(time_bucket)

    return schedule


def add_session_to_schedule(session: SESSION, schedule: list) -> Tuple[bool, Optional[str]]:
    """
    Check availability and add a session to the schedule.
    """
    try:
        start_time = session.start_time
        duration = session.duration
        machine_ids = session.machine_id

        # Find the starting time bucket
        for time_bucket in schedule:
            if time_bucket[0] == start_time:
                start_index = schedule.index(time_bucket)
                break
        else:
            return False, "Start time not found in schedule"

        # Calculate the number of time buckets the session spans
        num_buckets = -(-duration // TIME_BUCKET_SIZE) if duration else 1  # Default to 1 bucket if duration is None

        # Check availability and add the session's machines to the appropriate time buckets
        for i in range(num_buckets):
            if start_index + i >= len(schedule):
                return False, "Session exceeds schedule bounds"

            time_bucket = schedule[start_index + i]
            for machine_id in machine_ids:
                # Check if the machine is available
                if not any(m.machine_id == machine_id and m.status == Status.AVAILABLE for m in time_bucket[1:]):
                    return False, f"Machine {machine_id} unavailable at {time_bucket[0]}"

                # Create a MACHINE object for the session
                machine = MACHINE(
                    machine_id=machine_id,
                    session_id=session.session_id,
                    status=session.status,
                    scheduled_until=(session.start_time + session.duration) if session.duration else None,
                    last_updated=time.time(),
                    exchange_id=session.exchange_id,
                    origin_node=selfNode,
                    destination_node=Node.HANDLER
                )

                # Replace or add the machine in the time bucket
                for idx, m in enumerate(time_bucket[1:], start=1):
                    if m.machine_id == machine_id:
                        # Update the existing MACHINE object in the time bucket
                        time_bucket[idx] = machine
                        break
                else:
                    # If no matching machine ID is found, raise an error
                    return False, f"Machine ID {machine_id} not found in time bucket {time_bucket[0]}"

        return True, None

    except Exception as e:
        return False, "An unexpected error occurred while adding the session"


################################################################################################################
################################################################################################################
'''Incoming Message Handlers'''
#--------------------------------------------------------------------------------------------------------------#


def handle_session_proposal(session: SESSION):
    """
    Handle a proposed session by checking availability and adding it to the schedule.
    """
    global master_schedule

    try:

        #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ Add handling for making modifications to existing sessions

        # Determine the session's date
        session_date = session.start_time.strftime("%Y-%m-%d")
        current_date = datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d")

        # Load the appropriate schedule
        if session_date == current_date:
            # Use the shared dictionary for today's schedule
            schedule = master_schedule
            logger.info(f"Loaded today's schedule for session {session.session_id}")
        else:
            # Load the schedule from file for other dates
            schedule = load_master_schedule(session_date)
            logger.info(f"Loaded {session_date} schedule for session {session.session_id}")
        
        # Check availability and add the session to the schedule  
        added, conflict_message = add_session_to_schedule(session, schedule)
        
        if added:
            # Send CONFIRMATION that session was added
            confirmation_message = CONFIRMATION(
                success=True,
                message=f"Session {session.session_id} added successfully",
                session_id=session.session_id,
                exchange_id=session.exchange_id,
                origin_node=selfNode,
                destination_node=session.origin_node
            )
            mqtt.publish(TOPIC_MAP[session.origin_node], confirmation_message.json())
            logger.info(f"Session {session.session_id} added successfully to {session_date} schedule")
            # Save the updated schedule to file
            save_master_schedule(schedule, session_date)
            # Add session to master session list and save to file
            master_session_list.append(session)
            save_master_session_list(master_session_list)
            # Update today's schedule if the session is for today
            if session_date == current_date:
                master_schedule = schedule
                logger.info(f"Updated today's schedule with session {session_date}")
        else:
            # Send CONFIRMATION that session failed to add
            confirmation_message = CONFIRMATION(
                success=False,
                message=f"Failed to add session {session.session_id}: {conflict_message}",
                session_id=session.session_id,
                exchange_id=session.exchange_id,
                origin_node=selfNode,
                destination_node=session.origin_node
            )
            mqtt.publish(TOPIC_MAP[session.origin_node], confirmation_message.json())
            logger.warning(f"Failed to add session {session.session_id}: {conflict_message}")    
    
    except Exception as e:
        logger.error(f"Failed to handle session proposal: {e}")

def handle_schedule_request(request: REQUEST):
    """
    Handle a schedule request by sending the requested schedule.
    """
    try:
        # Determine the requested date
        date = request.date if request.date else datetime.fromtimestamp(request.timestamp).strftime("%Y-%m-%d")
        current_date = datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d")
        
        # Load the appropriate schedule
        if date == current_date:
            # Use the shared dictionary for today's schedule
            schedule = master_schedule
        else:
            # Load the schedule from file for other dates
            schedule = load_master_schedule(date)

        # Create a SCHEDULE message
        schedule_message = SCHEDULE(
            date=date,
            schedule=schedule,
            exchange_id=request.exchange_id,
            origin_node=selfNode,
            destination_node=request.origin_node
        )

        # Send the schedule message
        mqtt.publish(TOPIC_MAP[request.origin_node], schedule_message.json())
        logger.info(f"Sent schedule for {date} to {request.origin_node}")

    except Exception as e:
        logger.error(f"Failed to handle schedule request: {e}")

def handle_session_request(request: REQUEST):
    """
    Handle a session request by sending the requested session.
    """
    global master_session_list

    try:
        # Find the requested session
        session = next((s for s in master_session_list if s.session_id == request.session_id), None)
        if not session:
            logger.warning(f"Session ID {request.session_id} not found")
            return

        # Create a SESSION message
        session_message = SESSION(
            session=session.session_id,
            machine_id=session.machine_id,
            status=session.status,
            start_time=session.start_time,
            duration=session.duration,
            time_created=session.time_created,
            exchange_id=request.exchange_id,
            origin_node=selfNode,
            destination_node=request.origin_node
        )

        # Send the session message
        mqtt.publish(TOPIC_MAP[request.origin_node], session_message.json())
        logger.info(f"Sent session {request.session_id} to {request.origin_node}")

    except Exception as e:
        logger.error(f"Failed to handle session request: {e}")

async def incoming_message_processor(topic: str, message: str):
    """
    Handle incoming messages on the internal/manager topic.
    """
    logger.info(f"Received message: {message}") 
    try:
        try:
            # Parse as SESSION
            session = SESSION.parse_raw(message)
            logger.info(f"Received proposed session: {session.session_id} from {session.origin_node}")

            # Handle session proposal
            handle_session_proposal(session)

            return

        except Exception:
            pass  # Not a SESSION message

        try:
            # Parse as REQUEST
            request = REQUEST.parse_raw(message)
            logger.info(f"Received request for {request.request_type} from {request.origin_node}")

            if request.request_type == Request.SCHEDULE:
                # Handle schedule request
                handle_schedule_request(request)

            elif request.request_type == Request.SESSION:
                # Handle session request
                handle_session_request(request)

            else:
                logger.warning(f"Unable to handle request type: {request.request_type}")

            return

        except Exception:
            pass  # Not a REQUEST message

        logger.warning(f"Received unexpected message type on {MANAGER_TOPIC}")

    except Exception as e:
        logger.error(f"Failed to process message: {e}")
