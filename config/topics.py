from utils import Node

# === Internal Topics ===

# Schedule manager receives new sessions and requests for schedule or status through this topic
MANAGER_TOPIC = "internal/manager"

# Machine handler receives machine updates and requests for machine info through this topic
HANDLER_TOPIC_INTERNAL = "internal/handler"

# Kiosk interface receives requested sessions and schedules, as well as confirmations for new sessions through this topic
KIOSK_TOPIC = "internal/kiosk"

# Reservation interface receives requested sessions and schedules, as well as confirmations for new sessions through this topic
RESERVATION_TOPIC = "internal/reservation"

# Admin portal receives requested sessions and schedules, as well as confirmations for session changes and requested machine info through this topic
ADMIN_TOPIC = "internal/admin"


# === External Topics ===

# Communication to physical machines (ESP32s) sending machine updates and requests for info through this topic
MACHINE_TOPIC_BASE = "external/machine/{id}"

# Machine handler receives confirmations of machine updates and requested machine info through this topic
HANDLER_TOPIC_EXTERNAL = "external/handler"

TOPIC_MAP = {
    Node.KIOSK: KIOSK_TOPIC,
    Node.ADMIN: ADMIN_TOPIC,
    Node.RESERVATION: RESERVATION_TOPIC,
    Node.HANDLER: HANDLER_TOPIC_INTERNAL,
    Node.MANAGER: MANAGER_TOPIC
}

# === External Topic Helpers ===

def machine_topic(machine_id: int) -> str:
    """
    Returns the MQTT topic for communicating with a specific machine.
    
    Args:
        machine_id (str): The unique ID of the machine.
    
    Returns:
        str: Formatted MQTT topic string.
    """
    return MACHINE_TOPIC_BASE.format(id=str(machine_id))
