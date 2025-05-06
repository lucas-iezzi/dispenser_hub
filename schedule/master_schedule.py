# schedule/master_schedule.py

from threading import Lock

# The shared master schedule dictionary
master_schedule = {}
_schedule_lock = Lock()

# Simple boolean flag to indicate schedule change
_schedule_changed = False

def get_master_schedule():
    with _schedule_lock:
        return master_schedule.copy()

def set_master_schedule(new_schedule: dict):
    global master_schedule, _schedule_changed
    with _schedule_lock:
        master_schedule = new_schedule
        _schedule_changed = True

def update_schedule_entry(bucket_time: str, machine_id: str, session_data: dict):
    global _schedule_changed
    with _schedule_lock:
        if bucket_time not in master_schedule:
            master_schedule[bucket_time] = {}
        master_schedule[bucket_time][machine_id] = session_data
        _schedule_changed = True

def get_schedule_flag() -> bool:
    with _schedule_lock:
        return _schedule_changed

def clear_schedule_flag():
    global _schedule_changed
    with _schedule_lock:
        _schedule_changed = False
