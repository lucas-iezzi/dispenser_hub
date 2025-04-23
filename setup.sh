#!/bin/bash

set -e

echo ">>> Updating and installing system dependencies..."
sudo apt update
sudo apt install -y git dnsmasq mosquitto mosquitto-clients python3-pip

echo ">>> Installing Python dependencies (paho-mqtt, pydantic)..."
pip3 install --upgrade --break-system-packages paho-mqtt pydantic || echo "Ignoring pip errors due to system-wide installation restrictions."

echo ">>> Enabling services to start on boot..."
sudo systemctl enable dnsmasq
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

echo ">>> Configuring static IP on eth0..."
if ! grep -q "interface eth0" /etc/dhcpcd.conf; then
  sudo bash -c 'echo -e "\ninterface eth0\nstatic ip_address=192.168.4.1/24" >> /etc/dhcpcd.conf'
else
  echo "Static IP for eth0 already configured."
fi

echo ">>> Configuring dnsmasq for Ethernet DHCP..."
if ! grep -q "interface=eth0" /etc/dnsmasq.conf; then
  sudo bash -c 'cat <<EOF >> /etc/dnsmasq.conf

interface=eth0
dhcp-range=192.168.4.10,192.168.4.100,255.255.255.0,24h
EOF'
else
  echo "DHCP config for eth0 already present."
fi

echo ">>> Configuring Mosquitto to bind only to 192.168.4.1..."
if ! grep -q "listener 1883 192.168.4.1" /etc/mosquitto/mosquitto.conf; then
  sudo bash -c 'cat <<EOF >> /etc/mosquitto/mosquitto.conf

listener 1883 192.168.4.1
allow_anonymous true
EOF'
else
  echo "Mosquitto config already present."
fi

echo ">>> Cloning dispenser_hub repo into /home/pi..."
if [ ! -d "/home/pi/dispenser_hub" ]; then
  cd /home/pi
  git clone https://github.com/lucas-iezzi/dispenser_hub.git
else
  echo "Repo already exists. Pulling latest changes..."
  cd /home/pi/dispenser_hub
  git pull
fi
