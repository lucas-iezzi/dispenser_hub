# machine_handler.py

import asyncio
from mqtt.mqtt_client import mqtt
from config import (
    INTERNAL_HANDLER_TOPIC,
    INTERNAL_MANAGER_TOPIC,
    EXTERNAL_MACHINE_TOPIC_BASE,
    EXTERNAL_HANDLER_TOPIC,
    external_machine_topic,
)
from utils.messages import Machine, Confirmation, Request
from utils.logger import get_logger

logger = get_logger("machine_handler")

# Async message queue to process confirmations coming back from machines
confirmation_queue = {}

async def handle_internal_handler_message(message: str):
    """
    Callback for messages received on INTERNAL_HANDLER_TOPIC.
    Message can be a Machine (status update) or Request (machine info request).
    """
    try:
        # Try to parse as Machine
        machine_update = Machine.parse_raw(message)
        logger.info(f"Received machine update for ID {machine_update.machine_id}")

        topic = external_machine_topic(machine_update.machine_id)
        exchange_id = machine_update.exchange_id

        # Save exchange ID for this machine so we can track response
        confirmation_queue[exchange_id] = {
            "origin": "status_update",
            "machine": machine_update,
        }

        mqtt.publish(topic, machine_update.json())
        logger.info(f"Forwarded machine update to {topic}")

    except Exception:
        # If it fails to parse as Machine, try Request
        try:
            request = Request.parse_raw(message)
            logger.info(f"Received request for machine ID {request.machine_id}")

            if request.type != "machine":
                logger.warning("Request type is not 'machine'; ignoring.")
                return

            topic = external_machine_topic(request.machine_id)
            exchange_id = request.exchange_id

            confirmation_queue[exchange_id] = {
                "origin": "request",
                "request": request,
            }

            mqtt.publish(topic, request.json())
            logger.info(f"Forwarded machine info request to {topic}")

        except Exception as e:
            logger.error(f"Failed to parse message on {INTERNAL_HANDLER_TOPIC}: {e}")

def main():
    mqtt.subscribe(INTERNAL_HANDLER_TOPIC, handle_internal_handler_message)
    mqtt.subscribe(EXTERNAL_HANDLER_TOPIC, handle_external_handler_message)  # Will define this next

    logger.info("Machine handler started and subscribed to topics.")
    asyncio.get_event_loop().run_forever()

