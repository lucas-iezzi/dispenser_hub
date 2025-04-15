# driving_range_dispenser
Raspberry Pi Architecture to control driving range in bay golf ball dispenser with MQTT communication to dispensers over local network and web connection to AWS server for integration with 3rd party webservices

# Setup DHCP and MQTT over Ethernet on Raspberry Pi

## 1. Install Mosquitto Broker

```bash
sudo apt update
sudo apt install -y mosquitto mosquitto-clients
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
