# schedule/scheduler.py

from datetime import datetime
from typing import List, Optional, Union
from utils import Status
from utils import get_logger
#from utils import session_id_generator, exchange_id_generator
from config import TIME_BUCKET_SIZE, BUFFER_SIZE
from config import MACHINE_LAYOUT
from schedule.master_schedule import get_master_schedule
from messages import SESSION

logger = get_logger("scheduler")

"""
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
Need to add functions in utils to define session_id and exchange_id and to handle old ids
Implement these functions in machine and session creation here
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
"""


def are_adjacent(machine_ids: Union[int, List[int]]) -> bool:
    """
    Returns True if all machine_ids are in the same row of MACHINE_LAYOUT
    and are consecutive in that row.
    """
    if isinstance(machine_ids, int):
        machine_ids = [machine_ids]

    for row in MACHINE_LAYOUT:
        try:
            indices = [row.index(mid) for mid in machine_ids]
            # Check they are sorted and consecutive
            if sorted(indices) == list(range(min(indices), max(indices) + 1)):
                return True
        except ValueError:
            continue
    return False

def check_availability(machine_ids: Union[int, List[int]], start_time: datetime, duration: int, schedule: Optional[List[List]] = None) -> bool:
    if isinstance(machine_ids, int):
        machine_ids = [machine_ids]
        
    duration_idx = int(duration / TIME_BUCKET_SIZE) # Converts duration from seconds into number of time buckets
    date = datetime.now().strftime("%Y-%m-%d")

    if schedule is None:
        schedule = get_master_schedule(date)

    # Find index of the start time bucket
    start_idx = next(
        (i for i, bucket in enumerate(schedule) if abs((bucket[0] - start_time).total_seconds()) < TIME_BUCKET_SIZE.total_seconds()/2),  # Returns the closest bucket index to the start time
        None
    )
    if start_idx is None:
        return False  # Start time doesn't align with any known time bucket

    total_buckets = len(schedule)

    # Check reservation window
    for offset in range(duration):
        index = start_idx + offset
        if index < 0 or index >= total_buckets:
            return False  # Reservation outside of the schedule
        bucket = schedule[index][1:]
        if not all(m.status == Status.AVAILABLE and m.machine_id in machine_ids for m in bucket if m.machine_id in machine_ids):  # Checks if all machines are available in time block
            return False

    # Check buffer before
    for b in range(1, BUFFER_SIZE + 1):
        index = start_idx - b
        if index < 0 or index >= total_buckets:
            continue  # Buffer not needed because reservation is at the beginning of the schedule
        bucket = schedule[index][1:]
        if not all(m.status == Status.AVAILABLE and m.machine_id in machine_ids for m in bucket if m.machine_id in machine_ids):  # Checks if all machines are available in time block
            return False

    # Check buffer after
    for b in range(1, BUFFER_SIZE + 1):
        index = start_idx + duration + b - 1
        if index < 0 or index >= total_buckets:
            continue  # Buffer not needed because reservation is at the end of the schedule
        bucket = schedule[index][1:]
        if not all(m.status == Status.AVAILABLE and m.machine_id in machine_ids for m in bucket if m.machine_id in machine_ids):  # Checks if all machines are available in time block
            return False

    return True

def get_availability(date: str, number_of_machines: int, start_time: Optional[datetime] = None, duration: int = 3600) -> Union[List[SESSION], bool]:
    schedule = get_master_schedule(date)
    options = []
    duration_idx = int(duration / TIME_BUCKET_SIZE)  # Converts duration from seconds to number of time buckets

    for idx in range(len(schedule) - duration_idx):  # Iterate through schedule where session could fit
        candidate_bucket = schedule[idx]
        machines = candidate_bucket[1:]  # Strip timestamp from time bucket

        # Try every contiguous group of available machines
        for start_pos in range(len(machines) - number_of_machines + 1):
            group = machines[start_pos:start_pos + number_of_machines]

            # Ensure all machines in the group are AVAILABLE at the proposed start time
            if not all(m.status == Status.AVAILABLE for m in group):
                continue

            machine_ids = [m.machine_id for m in group]

            # Check if all machines in the group are available for full duration and buffer
            if not check_availability(
                machine_ids=machine_ids,
                start_time=candidate_bucket[0],
                duration=duration,
                schedule=schedule
            ):
                continue  # Skip this group if any machine is not available in any bucket

            # Ensure selected machines are adjacent (i.e., suitable group)
            if not are_adjacent(machine_ids):
                continue

            # Construct a session object for the valid group
            session = SESSION(
                machine_ids=machine_ids,
                session_id=12345,  # Replace with actual session ID generation logic
                status=Status.RESERVED,
                start_time=candidate_bucket[0],
                duration=duration
            )
            options.append(session)

    # If a preferred start time is given, sort sessions by proximity to that time
    if start_time:
        options.sort(key=lambda s: abs((s.start_time - start_time).total_seconds()))

    return options if options else False

def add_session(session: SESSION) -> bool:
    schedule = get_master_schedule(session.date)  # Load the schedule for the given date

    # Use check_availability to validate the requested session time
    if not check_availability(
        machine_ids=session.machine_ids,
        start_time=session.start_time,
        duration=session.duration,
        schedule=schedule
    ):
        logger.warning(f"Cannot add session {session.session_id}: machines not available for requested time.")
        return False

    # Get the list of time bucket indices this session occupies
    bucket_indices = get_time_bucket_range(schedule, session.start_time, session.end_time)
    if not bucket_indices:
        logger.error("Could not find valid time buckets for the session.")
        return False

    # Reserve the machines by updating their status and attaching the session ID
    for idx in bucket_indices:
        time_bucket = schedule[idx]
        for i, machine in enumerate(time_bucket[1:], start=1):
            if machine.machine_id in session.machine_ids:
                time_bucket[i].status = Status.RESERVED
                time_bucket[i].session_id = session.session_id
                time_bucket[i].timestamp = time.time()

    # Save the updated schedule
    update_master_schedule(session.date, schedule)
    logger.info(f"Session {session.session_id} added for machines {session.machine_ids} on {session.date}")
    return True

