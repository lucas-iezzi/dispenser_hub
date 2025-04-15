Raspberry Pi Architecture to control driving range in bay golf ball dispenser with MQTT communication to dispensers over local network and web connection to AWS server for integration with 3rd party webservices.  To set this up

# Setup Raspberry Pi

## 1. Install dependencies
```
sudo apt update && sudo apt install -y git dnsmasq mosquitto mosquitto-clients
sudo systemctl enable dnsmasq
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```
## 2. Set Static IP on Ethernet Port
a. Edit DHCP config:
```
sudo nano /etc/dhcpcd.conf
```
b. Add to the end of the file:
```
interface eth0
static ip_address=192.168.4.1/24
```
c. Save and exit: `Ctrl+O`, `Enter`, then `Ctrl+X`  
d. Reboot:
```
sudo reboot
```
e. Confirm IP:
```
ip addr show eth0
```
## 3. Configure DHCP using `dnsmasq`
a. Edit config:
```
sudo nano /etc/dnsmasq.conf
```
b. Add to the end:
```
interface=eth0
# Set IP range from .10 to .100 (expandable later)
dhcp-range=192.168.4.10,192.168.4.100,255.255.255.0,24h
```
c. Save and exit: `Ctrl+O`, `Enter`, then `Ctrl+X`  
d. Restart `dnsmasq`:
```
sudo systemctl restart dnsmasq
```
e. Check status:
```
sudo systemctl status dnsmasq
```
## 4. Configure `mosquitto` to Bind Only to Ethernet
a. Edit config file:
```
sudo nano /etc/mosquitto/mosquitto.conf
```
b. Add to the end:
```
# Start listener on TCP port 1883, bind to Ethernet IP (use "0.0.0.0" for all interfaces)
listener 1883 192.168.4.1
# Allow anonymous access (set to false and use "password_file /etc/mosquitto/passwd" for
authentication)
allow_anonymous true
```
c. Save and exit: `Ctrl+O`, `Enter`, then `Ctrl+X` 
d. Reboot:
```
sudo reboot
```
## 5. Test MQTT
```
mosquitto_sub -h 192.168.4.1 -t test/topic &
mosquitto_pub -h 192.168.4.1 -t test/topic -m "Hello IoT"
```
## 6. Import `dispenser_hub` Code onto Raspberry Pi
a. Clone `dispenser_hub` repo onto Pi
```
cd /home/{username}
git clone https://github.com/lucas-iezzi/driving_range_dispenser/dispenser_hub.git
```
c. Run `setup_test.py` to finish setup and test
```
python /dispenser_hub/tests/setup_test.py
```

#
# Description for Vibe Coding Context

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

### Core Topics

- `machines/commands` – All status update commands go here.
- `machines/{id}/update` – Outbound messages from `machine_handler` to control machines.
- `machines/{id}/response` – Acknowledgments from machines after receiving commands.

### Node-Specific Response Topics

- `machines/responses/{origin_node}` – Acknowledgment or error responses from `machine_handler` to the origin node.

### Timer Topics

- `timer/set` – Timer requests from `machine_handler`.
- `timer/expired` – Notifies `machine_handler` to deactivate a machine after time expires.

### Status Request Topics

- `machines/status/request` – Any node can request current machine statuses.
- `machines/status/response` – `machine_handler` replies with current statuses.

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

## Next Steps

- Implement conflict resolution in `machine_handler`.
- Integrate full duration tracking with the timer node.
- Build UIs for kiosk and admin portal.
- Connect reservation and admin portals to cloud APIs.
