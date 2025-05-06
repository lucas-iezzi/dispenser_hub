# schedule/scheduler.py

from datetime import datetime, timedelta
from typing import List, Optional, Union

from utils.enums import Status
from utils.logger import get_logger
from utils.time import round_time_to_bucket, get_time_bucket_range, TIME_BUCKET_SIZE
from schedule.master_schedule import get_master_schedule, update_master_schedule
from messages import SESSION, MACHINE

logger = get_logger("scheduler")


def get_availability(date: str, number_of_machines: int, start_time: Optional[datetime] = None, duration: int = 1) -> Union[SESSION, List[SESSION], bool]:
    schedule = get_master_schedule(date)  # Load the schedule for the given date
    options = []  # Store valid session options

    # If a start time is provided, convert it to a time bucket index
    if start_time:
        base_bucket = round_time_to_bucket(start_time)  # Round time to nearest bucket
        base_index = next((i for i, tb in enumerate(schedule) if tb[0] == base_bucket), None)  # Find index of base bucket
        if base_index is None:
            logger.warning("Provided start time is not in today's schedule.")
            return False

        # Search within a window of +/- 5 time buckets
        search_indices = [base_index + offset for offset in range(-5, 6) if 0 <= base_index + offset < len(schedule)]
    else:
        # If no time is given, search the entire day
        search_indices = list(range(len(schedule) - duration))

    for idx in search_indices:
        candidate_machines = schedule[idx][1:]  # Machines in the current time bucket

        # Check all possible groups of adjacent machines
        for start_pos in range(len(candidate_machines) - number_of_machines + 1):
            group = candidate_machines[start_pos:start_pos + number_of_machines]  # Candidate machine group
            if all(m.status == Status.AVAILABLE for m in group):  # Ensure initial bucket is available
                valid = True
                for offset in range(1, duration):  # Check subsequent buckets
                    future_bucket = idx + offset
                    if future_bucket >= len(schedule):
                        valid = False  # Not enough future buckets
                        break
                    future_group = schedule[future_bucket][1:][start_pos:start_pos + number_of_machines]
                    if not all(m.status == Status.AVAILABLE for m in future_group):
                        valid = False  # One or more machines not available
                        break

                if valid:
                    machine_ids = [m.machine_id for m in group]  # Get IDs of available machines
                    start_ts = schedule[idx][0]  # Start time of the session
                    end_ts = schedule[idx + duration - 1][0] + TIME_BUCKET_SIZE  # End time based on duration
                    session = SESSION(
                        machine_ids=machine_ids,
                        date=date,
                        start_time=start_ts,
                        end_time=end_ts
                    )

                    if start_time:
                        return session  # Return immediately if exact match found
                    options.append(session)  # Otherwise, collect as an option
                    break  # Avoid collecting multiple options from the same bucket

    if options:
        return options  # Return all alternative options

    return False  # No availability found


def add_session(session: SESSION) -> bool:
    schedule = get_master_schedule(session.date)  # Load the schedule for the given date

    bucket_indices = get_time_bucket_range(schedule, session.start_time, session.end_time)  # Get relevant time bucket indices
    if not bucket_indices:
        logger.error("Could not find valid time buckets for the session.")
        return False

    # Check that each machine is available in all required time buckets
    for idx in bucket_indices:
        time_bucket = schedule[idx]
        for i, machine in enumerate(time_bucket[1:], start=1):
            if machine.machine_id in session.machine_ids and machine.status != Status.AVAILABLE:
                logger.warning(f"Machine {machine.machine_id} not available at {time_bucket[0]}")
                return False

    # Reserve machines by updating their status and attaching the session ID
    for idx in bucket_indices:
        time_bucket = schedule[idx]
        for i, machine in enumerate(time_bucket[1:], start=1):
            if machine.machine_id in session.machine_ids:
                time_bucket[i].status = Status.RESERVED  # Set machine as reserved
                time_bucket[i].session_id = session.session_id  # Link the session ID

    update_master_schedule(session.date, schedule)  # Save changes to the schedule
    logger.info(f"Session {session.session_id} added for machines {session.machine_ids} on {session.date}")
    return True
