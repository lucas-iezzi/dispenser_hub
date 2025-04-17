# machine_handler.py

import asyncio
import time
from mqtt import mqtt
from config import (
    HANDLER_TOPIC_INTERNAL,
    MANAGER_TOPIC,
    MACHINE_TOPIC_BASE,
    HANDLER_TOPIC_EXTERNAL,
    machine_topic,
)
from utils import MACHINE, CONFIRMATION, REQUEST
from utils import get_logger
from utils import Node

# Initialize the logger
logger = get_logger("machine_handler")

# Define the current node
selfNode = Node.HANDLER

# Async message queue to process confirmations coming back from machines
confirmation_queue = {}

def main():
    """
    Entry point for the machine_handler node. Sets up MQTT subscriptions and starts the event loop.
    """
    # Subscribe to the internal handler topic for machine updates and requests
    mqtt.subscribe(HANDLER_TOPIC_INTERNAL, processInternalMessageIngress)

    # Subscribe to the external handler topic for confirmations and machine responses
    mqtt.subscribe(HANDLER_TOPIC_EXTERNAL, processExternalMessageIngress)

    logger.info("Machine handler started and subscribed to topics.")
    
    # Start the asyncio event loop to keep the node running
    asyncio.get_event_loop().run_forever()

async def processInternalMessageIngress(message: str):
    """
    Callback for messages received on HANDLER_TOPIC_INTERNAL.
    Handles machine updates and requests for machine information.
    """
    try:
        # Try to parse as Machine
        machine_update = MACHINE.parse_raw(message)
        logger.info(f"Received machine update for ID {machine_update.machine_id}")

        topic = machine_topic(machine_update.machine_id)
        exchange_id = machine_update.exchange_id

        # Save the machine update directly in the confirmation queue
        confirmation_queue[exchange_id] = machine_update

        mqtt.publish(topic, machine_update.json())
        logger.info(f"Forwarded machine update to {topic}")

    except Exception:
        # If it fails to parse as Machine, try Request
        try:
            request = REQUEST.parse_raw(message)
            logger.info(f"Received request for machine ID {request.machine_id}")

            if request.request_type != "machine":
                logger.warning("Request type is not 'machine'; ignoring.")
                return

            topic = machine_topic(request.machine_id)
            exchange_id = request.exchange_id

            # Save the request directly in the confirmation queue
            confirmation_queue[exchange_id] = request

            mqtt.publish(topic, request.json())
            logger.info(f"Forwarded machine info request to {topic}")

        except Exception as e:
            logger.error(f"Failed to parse message on {HANDLER_TOPIC_INTERNAL}: {e}")


async def processExternalMessageIngress(message: str):
    """
    Callback for messages received on EXTERNAL_HANDLER_TOPIC.
    Handles confirmations and responses from machines.
    """
    try:
        # Try to parse as Confirmation
        confirmation = CONFIRMATION.parse_raw(message)
        logger.info(f"Received confirmation for exchange ID {confirmation.exchange_id}")

        exchange_id = confirmation.exchange_id
        if exchange_id not in confirmation_queue:
            logger.warning(f"Unknown exchange ID {exchange_id}; ignoring.")
            return

        # Retrieve the original message
        original_message = confirmation_queue.pop(exchange_id)

        # Validate the confirmation
        if not confirmation.success:
            logger.error(f"Confirmation for exchange ID {exchange_id} failed.")
            return

        # Forward the confirmation to the appropriate internal topic
        mqtt.publish(MANAGER_TOPIC, confirmation.json())
        logger.info(f"Forwarded confirmation to {MANAGER_TOPIC}")

    except Exception:
        # If it fails to parse as Confirmation, try Machine (response to a request)
        try:
            machine_response = MACHINE.parse_raw(message)
            logger.info(f"Received machine response for ID {machine_response.machine_id}")

            exchange_id = machine_response.exchange_id
            if exchange_id not in confirmation_queue:
                logger.warning(f"Unknown exchange ID {exchange_id}; ignoring.")
                return

            # Retrieve the original request
            original_request = confirmation_queue.pop(exchange_id)

            # Forward the machine response to the origin node
            machine_response.destination_node = original_request.origin_node
            mqtt.publish(MANAGER_TOPIC, machine_response.json())
            logger.info(f"Forwarded machine response to {MANAGER_TOPIC}")

        except Exception as e:
            logger.error(f"Failed to parse message on {HANDLER_TOPIC_EXTERNAL}: {e}")

async def cleanup_stale_confirmations(timeout: float = 30.0):
    """
    Periodically checks for stale entries in the confirmation queue and removes them.
    Sends a failure confirmation back to the schedule_manager for each stale entry.
    """
    while True:
        current_time = time.time()
        stale_keys = [
            exchange_id for exchange_id, message in confirmation_queue.items()
            if current_time - message.timestamp > timeout
        ]
        for exchange_id in stale_keys:
            # Retrieve the stale message
            stale_message = confirmation_queue.pop(exchange_id, None)
            if not stale_message:
                continue

            # Create a failure confirmation
            failure_confirmation = CONFIRMATION(
                success=False,
                exchange_id=exchange_id,
                machine_id=getattr(stale_message, "machine_id", None),
                session_id=getattr(stale_message, "session_id", None),
                status=getattr(stale_message, "status", None),
                origin_node=selfNode,  # Use selfNode for the current node
                destination_node=stale_message.origin_node,  # Original sender
                timestamp=time.time(),
            )

            # Publish the failure confirmation
            mqtt.publish(MANAGER_TOPIC, failure_confirmation.json())
            logger.warning(
                f"Stale confirmation for exchange ID {exchange_id} removed. "
                f"Failure confirmation sent to {MANAGER_TOPIC}."
            )

        # Sleep before the next cleanup cycle
        await asyncio.sleep(timeout)