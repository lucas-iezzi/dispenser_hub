from utils import Node

class Topics:

    # === Internal Topics ===

    MANAGER_PROPOSE_SESSION = "internal/manager/propose/session"
    MANAGER_REQUEST_SESSION = "internal/manager/request/session"

    MACHINE_UPDATE_INTERNAL = "internal/machine/update"
    MACHINE_ACK_INTERNAL = "internal/machine/acknowledge"
    MACHINE_ALERT_INTERNAL = "internal/machine/alert"

    KIOSK_SESSION_ACK = "internal/kiosk/acknowledge/session"
    KIOSK_SESSION_RESPONSE = "internal/kiosk/response/session"
    KIOSK_SCHEDULE_RESPONSE = "internal/kiosk/response/schedule"

    RESERVATION_SESSION_ACK = "internal/reservation/acknowledge/session"
    RESERVATION_SESSION_RESPONSE = "internal/reservation/response/session"
    RESERVATION_SCHEDULE_RESPONSE = "internal/reservation/response/schedule"

    ADMIN_SESSION_ACK = "internal/admin/acknowledge/session"
    ADMIN_SESSION_RESPONSE = "internal/admin/response/session"
    ADMIN_SCHEDULE_RESPONSE = "internal/admin/response/schedule"

    TEST_SESSION_ACK = "internal/test/acknowledge/session"
    TEST_SESSION_RESPONSE = "internal/test/response/session"
    TEST_SCHEDULE_RESPONSE = "internal/test/response/schedule"

    # === External Topics ===

    MACHINE_UPDATE_BASE = "external/machine/{id}/update"
    MACHINE_ACK_BASE = "external/machine/{id}/acknowledge"
    MACHINE_ALERT_BASE = "external/machine/{id}/alert"

    HANDLER_TOPIC_EXTERNAL = "external/handler"

    # === External Topic Helpers ===

    @staticmethod
    def MACHINE_UPDATE_EXTERNAL(machine_id: int) -> str:
        return MACHINE_UPDATE_BASE.format(id=str(machine_id))

    @staticmethod
    def MACHINE_ACK_EXTERNAL(machine_id: int) -> str:
        return MACHINE_ACK_BASE.format(id=str(machine_id))

    @staticmethod
    def MACHINE_ALERT_EXTERNAL(machine_id: int) -> str:
        return MACHINE_ALERT_BASE.format(id=str(machine_id))

    '''
    TOPIC_MAP = {
        Node.KIOSK: KIOSK_TOPIC,
        Node.ADMIN: ADMIN_TOPIC,
        Node.RESERVATION: RESERVATION_TOPIC,
        Node.HANDLER: HANDLER_TOPIC_INTERNAL,
        Node.MANAGER: MANAGER_TOPIC
    }
    '''