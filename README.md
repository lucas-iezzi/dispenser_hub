Raspberry Pi Architecture to control driving range in bay golf ball dispenser with MQTT communication to dispensers over local network and web connection to AWS server for integration with 3rd party webservices.  To set this up

# System Architecture

![diagram](https://github.com/lucas-iezzi/dispenser_hub/blob/main/system_architecture.png)  

## Nodes


### `schedule_manager.py`
Handles master scheduling and session logic. Accepts incoming session requests, confirms additions to the schedule, resolves conflicts, and sends out updated session or schedule information. Also triggers machine actions based on the schedule.

**Receives from**:  
- `kiosk_interface.py`, `reservation_interface.py`, `admin_portal.py` (*Session*, *Request*)

**Publishes to**:  
- `machine_handler.py` (*Machine*)  
- `kiosk_interface.py`, `reservation_interface.py`, `admin_portal.py` (*Session*, *Schedule*, *Confirmation*)

---

### `machine_handler.py`
Manages the real-time status of machines. Acts as the authoritative internal controller of all machines. Handles incoming commands, forwards them to the respective physical machines, and monitors/report status. Integrates with a timer system to revert machine status after scheduled durations.

**Receives from**:  
- `schedule_manager.py` (*Machine*)  
- `admin_portal.py` (*Request*)  
- `machine_{id}` (*Machine*, *Confirmation*)

**Publishes to**:  
- `machine_{id}` (*Request*, *Machine*)  
- `admin_portal.py` (*Machine*)  
- `schedule_manager.py` (*Confirmation*) (optional for full loop closure)

---

### `machine_{id}`
Individual physical machine (ESP32 or similar). Executes machine control commands like activation/deactivation. Periodically reports machine state, ball level, or issues. May also confirm receipt of control messages.

**Receives from**:  
- `machine_handler.py` (*Machine*, *Request*)

**Publishes to**:  
- `machine_handler.py` (*Machine*, *Confirmation*)

---

### `kiosk_interface.py`
Handles in-person session creation and schedule display. Sends sessions to be scheduled and receives confirmations. Can also request the full schedule or session data.

**Receives from**:  
- `schedule_manager.py` (*Confirmation*, *Session*, *Schedule*)

**Publishes to**:  
- `schedule_manager.py` (*Session*, *Request*)

---

### `reservation_interface.py`
Manages online or mobile reservations. Allows users to view schedules and book future sessions. Works similarly to the kiosk, but typically with less time sensitivity.

**Receives from**:  
- `schedule_manager.py` (*Confirmation*, *Session*, *Schedule*)

**Publishes to**:  
- `schedule_manager.py` (*Session*, *Request*)

---

### `admin_portal.py`
Allows staff to view and modify schedules, request machine statuses, and receive machine reports. Can override machine status manually and monitor system health.

**Receives from**:  
- `schedule_manager.py` (*Confirmation*, *Session*, *Schedule*)  
- `machine_handler.py` (*Machine*)

**Publishes to**:  
- `schedule_manager.py` (*Session*, *Request*)  
- `machine_handler.py` (*Request*)


## MQTT Topics

### Topic Names Index

#### Internal Topics 
- `internal/manager` (*Session*, *Request*)
- `internal/handler` (*Machine*, *Request*)
- `internal/kiosk` (*Session*, *Schedule*, *Confirmation*)
- `internal/reservation`
- `internal/admin`

#### External Topics
- `external/machine/{id}`
- `external/handler`

### Message Types

#### Kiosk, Portal, Reservation → Schedule Manager (Session Ingress)

- **MQTT Topic**: `internal/manager`
- **Model Used**: *Session*
- **Purpose**: Brings in session booked at kiosk, booked online, and created by admin to be added to the master schedule
- **Origin Node**: `kiosk_interface.py`, `admin_portal.py`, `reservation_interface.py`
- **Destination Node**: `schedule_manager.py`

##### Example Payload:
```python
{
	"machine_id": [001,002]
	"session_id": 12345
	"status": "active"
	"start_time": 1673432480
	"duration": 3600
	"time_created": 1673432458.9977512
	"timestamp": 1673432458.9977512
	"origin_node": "kiosk_interface"
	"destination_node": "schedule_manager"
}
```

#### Schedule Manager → Kiosk, Portal, Reservation (Session Confirmation)

- **MQTT Topic**: `internal/kiosk`, `internal/reservation`, `internal/admin`
- **Model Used**: *Confirmation*
- **Purpose**: Confirms that status changes to the machine were received and accepted or rejected
- **Origin Node**: `schedule_manager.py`
- **Destination Node**: `kiosk_interface.py`

##### Example Payload:
```python
{
	"success": True
	"session_id": 12345
	"status": "active"
	"timestamp": 1673432459.1524629
	"origin_node": "schedule_manager"
	"destination_node": "kiosk_interface"
}
```

#### Kiosk, Admin, Reservation → Schedule Manager (Session Request)

- **MQTT Topic**: `internal/manager`
- **Model Used**: *Request*
- **Purpose**: Requests session information by session ID from schedule manager
- **Origin Node**: `kiosk_interface.py`, `admin_portal.py`, `reservation_interface.py`
- **Destination Node**: `schedule_manager.py`

##### Example Payload:
```python
{
	"request_id": 65833
	"request_type": "session"
	"timestamp": 1673432425.4624582
	"origin_node": "admin_portal"
	"destination_node": "schedule_manager"
}
```

#### Schedule Manager → Kiosk, Admin, Reservation (Session Broadcast)

- **MQTT Topic**: `internal/kiosk`, `internal/reservation`, `internal/admin`
- **Model Used**: *Session*
- **Purpose**: Relays information about current or future sessions by session ID to requesting nodes for checking and editing
- **Origin Node**: `schedule_manager.py`
- **Destination Node**: `kiosk_interface.py`, `admin_portal.py`, `reservation_interface.py`

##### Example Payload:
```python
{
	"machine_id": [001,002]
	"session_id": 12346
	"status": "active"
	"start_time": 1673457080
	"duration": 3600
	"time_created": 1673432494.7242571
	"timestamp": 1673435634.6573683
	"origin_node": "schedule_manager"
	"destination_node": "kiosk_interface"
}
```

#### Kiosk, Admin, Reservation → Schedule Manager (Schedule Request)

- **MQTT Topic**: `internal/manager`
- **Model Used**: *Request*
- **Purpose**: Requests master schedule from schedule manager
- **Origin Node**: `kiosk_interface.py`, `admin_portal.py`, `reservation_interface.py`
- **Destination Node**: `schedule_manager.py`

##### Example Payload:
```python
{
	"request_id": 65832
	"request_type": "schedule"
	"timestamp": 1673432425.4462713
	"origin_node": "kiosk_interface"
	"destination_node": "schedule_manager"
}
```

#### Schedule Manager → Kiosk, Admin, Reservation (Schedule Broadcast)

- **MQTT Topic**: `internal/kiosk`, `internal/reservation`, `internal/admin`
- **Model Used**: *Schedule*
- **Purpose**: Relays master schedule to requesting node to check availability and status of all machines
- **Origin Node**: `schedule_manager.py`
- **Destination Node**: `kiosk_interface.py`, `admin_portal.py`, `reservation_interface.py`

##### Example Payload:
```python
{
	"date": 1/11/2025
	"schedule":
	[
		...
		[10:30, Machine, Machine, Machine, ...],     # 5 minute interval
		[10:35, Machine, Machine, Machine, ...],     # 5 minute interval
		[10:40, Machine, Machine, Machine, ...],     # 5 minute interval
		...
	]
	"timestamp": 1673432956.5673920
	"origin_node": "schedule_manager"
	"destination_node": "reservation_interface"
}
```

#### Schedule Manager → Machine Handler (Machine Command)

- **MQTT Topic**: `internal/handler`
- **Model Used**: *Machine*
- **Purpose**: Triggers the machine handler to activate machines when sessions start, deactivate when sessions end, and change machine to idle or maintenance status per admin's request
- **Origin Node**: `schedule_manager.py`
- **Destination Node**: `machine_handler.py`

##### Example Payload:
```python
{
	"machine_id": 002
	"session_id": 54321
	"status": "active"
	"scheduled_until": 1673436080
	"timestamp": 1673432480.0124163
	"origin_node": "schedule_manager"
	"destination_node": "machine_handler"
}
```


#### Admin Portal → Machine Handler (Machine Report Request)

- **MQTT Topic**: `internal/handler`
- **Model Used**: *Request*
- **Purpose**: Requests that the machine send its information about ball level, status, end of scheduled time, etc to the machine handler
- **Origin Node**: `machine_handler.py`
- **Destination Node**: `machine_{id}`

##### Example Payload:
```python
{
	"request_type": "machine"
	"timestamp": 1673432425.4624582
	"origin_node": "machine_handler"
	"destination_node": "machine_004"
}
```

#### Machine Handler → Admin Portal (Machine Report)

- **MQTT Topic**: `internal/admin`
- **Model Used**: *Machine*
- **Purpose**: Provides information about ball levels and maintenance needed or errors were detected
- **Origin Node**: `machine_handler.py`
- **Destination Node**: `admin_portal.py`

##### Example Payload:
```python
{
	"machine_id": 004
	"status": "error"
	"ball_level": "low"
	"scheduled_until": 1673436080
	"timestamp": 1673433956.5143528
	"last_updated": 1673432480.0124163
	"origin_node": "machine_004"
	"destination_node": "admin_portal"
}
```

#### Machine Handler → Machine (Machine Request)

- **MQTT Topic**: `external/machine/{id}`
- **Model Used**: *Request*
- **Purpose**: Requests that the machine send its information about ball level, status, end of scheduled time, etc to the machine handler
- **Origin Node**: `machine_handler.py`
- **Destination Node**: `machine_{id}`

##### Example Payload:
```python
{
	"request_type": "machine"
	"timestamp": 1673432425.4624582
	"origin_node": "machine_handler"
	"destination_node": "machine_004"
}
```

#### Machine → Machine Handler (Machine Response)

- **MQTT Topic**: `external/handler`
- **Model Used**: *Machine*
- **Purpose**: Provides information about the machine to the machine handler either when information is requested or when action is needed
- **Origin Node**: `machine_{id}`
- **Destination Node**: `machine_handler.py`

##### Example Payload:
```python
{
	"machine_id": 004
	"status": "error"
	"ball_level": "low"
	"scheduled_until": 1673436080
	"timestamp": 1673433956.5143528
	"last_updated": 1673432480.0124163
	"origin_node": "machine_004"
	"destination_node": "machine_handler"
}
```

#### Machine Handler → Machine (Machine Control)

- **MQTT Topic**: `external/machine/{id}`
- **Model Used**: *Machine*
- **Purpose**: Changes physical machine status as specified by the machine handler and provides a timestamp to revert to the previous status if no new status is provided before then
- **Origin Node**: `machine_handler.py`
- **Destination Node**: `machine_{id}`

##### Example Payload:
```python
{
	"machine_id": 002
	"session_id": 54321
	"status": "active"
	"scheduled_until": 1673436080
	"timestamp": 1673432480.0124163
	"origin_node": "machine_handler"
	"destination_node": "machine_002"
}
```

#### Machine → Machine Handler (Machine Confirmation)

- **MQTT Topic**: `external/handler`
- **Model Used**: *Confirmation*
- **Purpose**: Confirms that status changes to the machine were received and accepted or rejected
- **Origin Node**: `machine_{id}`
- **Destination Node**: `machine_handler.py`

##### Example Payload:
```python
{
	"success": True
	"session_id": 54321
	"status": "active"
	"timestamp": 1673432480.2523466
	"origin_node": "machine_002"
	"destination_node": "machine_handler"
}
```

<br>
<br>
<br>
<br>

# Raspberry Pi Setup

## 1. Install dependencies
```bash
sudo apt update && sudo apt install -y git dnsmasq mosquitto mosquitto-clients
sudo systemctl enable dnsmasq
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```
## 2. Set Static IP on Ethernet Port
a. Edit DHCP config:
```bash
sudo nano /etc/dhcpcd.conf
```
b. Add to the end of the file:
```bash
interface eth0
static ip_address=192.168.4.1/24
```
c. Save and exit: `Ctrl+O`, `Enter`, then `Ctrl+X`  
d. Reboot:
```bash
sudo reboot
```
e. Confirm IP:
```bash
ip addr show eth0
```
## 3. Configure DHCP using `dnsmasq`
a. Edit config:
```bash
sudo nano /etc/dnsmasq.conf
```
b. Add to the end:
```ini
interface=eth0
# Set IP range from .10 to .100 (expandable later)
dhcp-range=192.168.4.10,192.168.4.100,255.255.255.0,24h
```
c. Save and exit: `Ctrl+O`, `Enter`, then `Ctrl+X`  
d. Restart `dnsmasq`:
```bash
sudo systemctl restart dnsmasq
```
e. Check status:
```bash
sudo systemctl status dnsmasq
```
## 4. Configure `mosquitto` to Bind Only to Ethernet
a. Edit config file:
```bash
sudo nano /etc/mosquitto/mosquitto.conf
```
b. Add to the end:
```ini
# Start listener on TCP port 1883, bind to Ethernet IP (use "0.0.0.0" for all interfaces)
listener 1883 192.168.4.1
# Allow anonymous access (set to false and use "password_file /etc/mosquitto/passwd" for
authentication)
allow_anonymous true
```
c. Save and exit: `Ctrl+O`, `Enter`, then `Ctrl+X` 
d. Reboot:
```bash
sudo reboot
```
## 5. Test MQTT
```bash
mosquitto_sub -h 192.168.4.1 -t test/topic &
mosquitto_pub -h 192.168.4.1 -t test/topic -m "Hello IoT"
```
## 6. Import `dispenser_hub` Code onto Raspberry Pi
a. Clone `dispenser_hub` repo onto Pi
```bash
cd /home/{username}
git clone https://github.com/lucas-iezzi/driving_range_dispenser/dispenser_hub.git
```
c. Run 'setup_test.py' to finish setup and test
```bash
python /dispenser_hub/tests/setup_test.py
```
<br>
<br>
<br>
<br>

# System Overview

## Summary

This is a Raspberry Pi–based local MQTT system designed to manage 20–80 IoT machines (e.g., ESP32s) in a driving range setting. The Pi acts as the command router and source of truth, coordinating activation and deactivation commands between various input sources (kiosk, reservation system, admin portal) and the machines. All communication is done over MQTT, and the system is designed for localized offline operation with optional cloud integration.

## Key Components

### 1. `machine_handler.py` (Core Logic Node)

- Central authority for real-time machine statuses.
- Listens for MQTT messages from other nodes.
- Parses messages using the shared `MachineCommand` Pydantic model.
- Updates internal `machine_states` dictionary and persists it to disk.
- Publishes control messages to the individual machines.
- Sends acknowledgments back to the origin node.
- Responds to any node that requests machine statuses.
- **Only this node can change machine statuses**, ensuring single-source-of-truth consistency.

#### Future Feature: Conflict Resolution

- Logic will detect conflicting or duplicate commands.
  - Identical commands from the same origin will be ignored.
  - Conflicting commands from different origins will result in one being rejected with a descriptive MQTT response.
- All handling will occur **before** any status changes or MQTT publishes.

### 2. Timer Node

- Regulates how long a machine remains active.
- Receives timer information from `machine_handler` upon activation.
- Waits for the specified duration and then sends a deactivation command back.
- Ensures that paid durations are accurately enforced.

### 3. Kiosk Node

- Interfaces with local or cloud payment systems.
- Provides UI for customer interaction and payment.
- Sends timed activation commands to `machine_handler` upon successful payment.
- Subscribes to status updates to provide real-time feedback to users.

### 4. Reservation System Node

- Connects to a cloud server via API.
- Handles online reservations and schedules.
- When a reservation time approaches, it sends a command to `machine_handler` to activate the machine.
- Periodically syncs reservations from the cloud.

### 5. Admin Portal Node

- A web dashboard for staff and management.
- Connects to cloud APIs for admin control.
- Can activate/deactivate machines, enable maintenance, adjust settings, etc.
- All changes must go through `machine_handler`, which also reports status updates.

## MQTT Topics

### Internal Request Topics

- `internal/machine_handler/command` – All machine update commands go through here.
- `internal/status/request` – Status requests from any node to `status_fetcher`.
- `internal/timer/set` – Timer requests from `machine_handler`.

### Internal Response Topics

- `internal/{origin_node}/response` – Acknowledgment or error responses from `machine_handler` to the origin node..
- `internal/{origin_node}/status` – Status response from `status_fetcher` back to the node which requested.

### External Topics

- `machines/{id}/update` – Outbound messages from `machine_handler` to control machines.
- `machines/{id}/response` – Acknowledgments from machines after receiving commands.

## Network & System Setup

- Raspberry Pi hosts all logic, MQTT broker, and local networking.
- Static IP: `192.168.4.1` on Ethernet.
- `dnsmasq` for DHCP.
- `mosquitto` bound to Ethernet interface.
- External cloud services are accessed via the Pi when needed.

## Deployment

- Run `update_code.sh` to update code from GitHub.
- Repository: `https://github.com/lucas-iezzi/dispenser_hub`
- Local path: `/home/engineering/dispenser_hub`

## Codebase Organization
```
/home/engineering/dispenser_hub/  
├── main.py                          # Optional launcher  
├── config/  
│   ├── __init__.py  
│   ├── settings.yaml                # Common settings (broker IP, ports, timeouts)  
│   └── topics.py                    # Source for all topic names  
├── mqtt/  
│   ├── __init__.py  
│   └── mqtt_client.py               # Shared MQTT client wrapper  
├── nodes/  
│   ├── machine_handler.py           # Core status control and MQTT logic  
│   ├── timer.py                     # Duration timer node  
│   ├── kiosk_interface.py           # Local kiosk purchase logic  
│   ├── reservation_interface.py     # Pulls from 3rd party reservation APIs  
│   └── admin_portal_interface.py    # Web UI hooks  
├── utils/  
│   ├── __init__.py  
│   ├── messages.py       			  # Uses pydantic for standardized message formats  
│   └── logger.py                    # Simple centralized logging utility  
├── tests/  
│   └── test_machine_handler.py  
```

