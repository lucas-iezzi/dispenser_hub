# schedule/file_io.py

import os
import json
from datetime import datetime, timedelta
from typing import List

from utils.logger import get_logger
from messages import MACHINE
from utils.enums import Status

logger = get_logger("file_io")

# Constants
SCHEDULE_PATH = "data/master_schedule.json"
TIME_BUCKET_SIZE = 5 * 60  # 5 minutes in seconds

# You may want to pass this in from the main script, or define a default set for testing
machine_id_list: List[int] = [1,2,3,4,5,6,7,8,9,10]

def generate_blank_schedule(date: str, machines: List[int]) -> List[list]:
    """
    Generate a blank schedule for a given date.
    Each time bucket contains a timestamp and one MACHINE object per machine.
    """
    start_of_day = datetime.strptime(date, "%Y-%m-%d")
    intervals_per_day = (24 * 60 * 60) // TIME_BUCKET_SIZE

    schedule = []
    for i in range(intervals_per_day):
        timestamp = int((start_of_day + timedelta(seconds=TIME_BUCKET_SIZE * i)).timestamp())
        time_bucket = [timestamp]

        for machine_id in machines:
            machine = MACHINE(
                machine_id=machine_id,
                status=Status.AVAILABLE,
            )
            time_bucket.append(machine)

        schedule.append(time_bucket)

    logger.info(f"Generated blank schedule for {date} with {len(machines)} machines.")
    return schedule

def save_schedule_to_disk(date: str, schedule: List[list]) -> bool:
    """Serialize the schedule and write to disk."""

    # Ensure the schedules directory exists
    schedules_dir = "schedules"
    os.makedirs(schedules_dir, exist_ok=True)

    # Construct the full file path
    filename = os.path.join(schedules_dir, f"{date}_schedule.json")

    try:
        # Convert MACHINE objects to dictionaries for JSON storage
        raw_schedule = []
        for time_bucket in schedule:
            timestamp = time_bucket[0]
            machines = [m.model_dump() for m in time_bucket[1:]]
            raw_schedule.append([timestamp] + machines)
        
        # Save the JSON data
        with open(filename, "w") as file:
            json.dump(raw_schedule, file, indent=4)  # Use indent=4 for readability

        logger.info(f"Master schedule for {date} saved successfully to {filename}.")
        return True
    
    except Exception as e:
        logger.error(f"Failed to save master schedule for {date} to {filename}: {e}")
        return False

def load_schedule_from_disk(date: str) -> List[list]:
    """Load the schedule from disk and reconstruct MACHINE models."""

    # Construct the full file path
    schedules_dir = "schedules"
    filename = os.path.join(schedules_dir, f"{date}_schedule.json")

    # Check if schedule already exists
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
    # Create blank schedule and save if schedule doesn't exist
    else:
        logger.warning(f"Master schedule for {date} not found in {filename}. Generating a blank schedule.")
        schedule = generate_blank_schedule(date)
        save_schedule_to_disk(date, schedule)
        return schedule
