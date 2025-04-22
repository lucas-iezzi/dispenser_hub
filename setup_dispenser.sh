###setup_dispenser.sh

#!/bin/bash

set -e
echo "Starting Dispenser Setup..."

### 1. Install Dependencies
echo "Installing dependencies..."
sudo apt update
sudo apt install -y git dnsmasq mosquitto mosquitto-clients paho-mqtt pydantic

### 2. Enable Services
echo "Enabling Mosquitto and dnsmasq services..."
sudo systemctl enable mosquitto
sudo systemctl enable dnsmasq

### 3. Set Static IP on eth0
echo "Setting static IP on eth0..."
if ! grep -q "interface eth0" /etc/dhcpcd.conf; then
    echo -e "\ninterface eth0\nstatic ip_address=192.168.4.1/24" | sudo tee -a /etc/dhcpcd.conf
else
    echo "Static IP already set in /etc/dhcpcd.conf"
fi

### 4. Configure DHCP (dnsmasq)
echo "Configuring dnsmasq for DHCP..."
DNSMASQ_CONFIG=$(cat <<EOF
interface=eth0
dhcp-range=192.168.4.10,192.168.4.100,255.255.255.0,24h
EOF
)
echo "$DNSMASQ_CONFIG" | sudo tee /etc/dnsmasq.conf > /dev/null

### 5. Configure Mosquitto
echo "Configuring Mosquitto..."
MOSQUITTO_CONFIG=$(cat <<EOF
listener 1883 192.168.4.1
allow_anonymous true
EOF
)
echo "$MOSQUITTO_CONFIG" | sudo tee /etc/mosquitto/mosquitto.conf > /dev/null

### 6. Reboot Networking Stack
echo "Restarting networking and services..."
sudo systemctl restart dhcpcd
sudo systemctl restart dnsmasq
sudo systemctl restart mosquitto

### 7. Clone dispenser_hub Repo
echo "Cloning GitHub repository..."
cd /home/pi || exit 1
if [ ! -d "dispenser_hub" ]; then
    git clone https://github.com/lucas-iezzi/driving_range_dispenser.git dispenser_hub
else
    echo "Repo already exists. Pulling latest..."
    cd dispenser_hub && git pull
fi

### 8. Run Python Setup Test (optional)
echo "Running setup test..."
python3 /home/pi/dispenser_hub/tests/setup_test.py || echo "⚠️ Python setup test failed."

echo "Setup complete. You should reboot the system now."
