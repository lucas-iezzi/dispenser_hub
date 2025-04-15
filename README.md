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
