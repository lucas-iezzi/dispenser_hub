# schedule/manager.py

import json
from pydantic import ValidationError
from typing import Callable
from scheduler import check_availability, add_session
from utils.messages import SESSION, Acknowledge  # SESSION is the incoming session proposal
from config.topics import Topics
from schedule.master_schedule import clear_dirty_flag
from utils import get_logger
from mqtt import MQTTClient, MQTTConfig

logger = getLogger("manager")

mqtt_client = MQTTClient(
    broker_host=MQTTConfig.BROKER_HOST,
    broker_port=MQTTConfig.BROKER_PORT,
    client_id="Manager"
)
mqtt_client.connect()

def start():
    logger.info("Starting schedule manager...")
    mqtt_client.loop_forever()

def handle_session_proposal(payload: dict):
    """Handle an incoming session proposal from an external source."""
    try:
        session = SESSION(**payload)
    except ValidationError as e:
        logger.error(f"Invalid session proposal format: {e}")
        response = ACKNOWLEDGE(success=False, message="Invalid session format")
        mqtt_client.publish(Topics.TEST_SESSION_RESPONSE, response.model_dump())
        return

    # Check availability
    is_available = check_availability(
        machine_ids=session.machine_ids,
        start_time=session.start_time,
        duration=session.duration
    )

    if not is_available:
        logger.info(f"Session proposal rejected due to unavailability: {session}")
        response = ACKNOWLEDGE(success=False, message="Requested time or machines are unavailable", session_id=session.session_id, exchange_id=session.exchange_id)
        mqtt_client.publish(Topics.TEST_SESSION_RESPONSE, response.model_dump())
        return

    # Attempt to add the session
    success = add_session(session)
    if success:
        logger.info(f"Session successfully added: {session}")
        clear_dirty_flag()  # Reset schedule change flag if used
        response = Acknowledge(success=True, message="Session added successfully", session_id=session.session_id, exchange_id=session.exchange_id)
    else:
        logger.warning(f"Failed to add session despite availability: {session}")
        response = Acknowledge(success=False, message="Failed to add session", session_id=session.session_id, exchange_id=session.exchange_id)

    mqtt_client.publish(Topics.TEST_SESSION_RESPONSE, response.model_dump())


def init_schedule_manager():
    """Initialize the schedule manager and subscribe to relevant topics."""
    logger.info("Initializing schedule manager...")
    mqtt_client.subscribe(Topics.MANAGER_PROPOSE_SESSION, handle_session_proposal)

if __name__ == "__main__":
    start()