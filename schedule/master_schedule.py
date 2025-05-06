# schedule/master_schedule.py

from threading import Lock
from datetime import datetime
from typing import List, Dict, Any
from utils.logger import get_logger

from schedule.file_io import load_schedule_from_disk, save_schedule_to_disk

logger = get_logger("master_schedule")

# Shared master schedule dictionary and lock
master_schedule: Dict[str, List[list]] = {}
_schedule_lock = Lock()
_today_changed = False

def get_master_schedule(date: str) -> List[list]:
    with _schedule_lock:
        try:
            # If schedule currently loaded
            return master_schedule[date].copy()
        except:
            # Otherwise load schedule
            logger.info("Date does not exist in master schedule. Pulling from disk")
            master_schedule[date] = load_schedule_from_disk(date)
            return master_schedule[date].copy()

def update_master_schedule(date: str, new_schedule: List[list]):
    global master_schedule, _today_changed
    with _schedule_lock:
        try:
            # Save the new schedule to the shared dict and to appropriate file on disk
            master_schedule[date] = new_schedule
            save_schedule_to_disk(date, new_schedule)
            
            # Raise the update flag if schedule changed is today
            today_date = datetime.now().strftime("%Y-%m-%d")
            if today_date == date:
                _today_changed = True
                logger.debug("Master schedule updated for today. Flag set.")
            else:
                logger.debug("Master schedule updated.")
            
        except:
            logger.error("Master schedule failed to update.")

def get_schedule_flag() -> bool:
    with _schedule_lock:
        return _today_changed

def clear_schedule_flag():
    global _today_changed
    with _schedule_lock:
        _today_changed = False
        logger.debug("Machines updated to match schedule. Update flag cleared.")

def clear_past_schedules():
    ### This function should run periodically, maybe every day or so and pop master_schedule entries with a date that has already passed.
    pass