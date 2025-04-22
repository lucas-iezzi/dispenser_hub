#!/bin/bash

set -e

echo ">>> Updating and installing system dependencies..."
sudo apt update
sudo apt install -y git dnsmasq mosquitto mosquitto-clients python3-pip

echo ">>> Setting up Python virtual environment..."
python3 -m venv /home/pi/venv
source /home/pi/venv/bin/activate

echo ">>> Installing Python dependencies (paho-mqtt, pydantic)..."
pip install --upgrade paho-mqtt pydantic

echo ">>> Enabling VNC..."
sudo raspi-config nonint do_vnc 0

echo ">>> Enabling MQTT and DHCP services..."
sudo systemctl enable dnsmasq
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

echo ">>> Configuring static IP on eth0..."
if ! grep -q "interface eth0" /etc/dhcpcd.conf; then
  sudo bash -c 'echo -e "\ninterface eth0\nstatic ip_address=192.168.4.1/24" >> /etc/dhcpcd.conf'
else
  echo "Static IP for eth0 already configured in /etc/dhcpcd.conf"
fi

echo ">>> Configuring dnsmasq for Ethernet DHCP..."
if ! grep -q "interface=eth0" /etc/dnsmasq.conf; then
  sudo bash -c 'cat <<EOF >> /etc/dnsmasq.conf

interface=eth0
dhcp-range=192.168.4.10,192.168.4.100,255.255.255.0,24h
EOF'
else
  echo "DHCP configuration for eth0 already exists in /etc/dnsmasq.conf"
fi

echo ">>> Configuring mosquitto to bind to Ethernet interface only..."
if ! grep -q "listener 1883 192.168.4.1" /etc/mosquitto/mosquitto.conf; then
  sudo bash -c 'cat <<EOF >> /etc/mosquitto/mosquitto.conf

listener 1883 192.168.4.1
allow_anonymous true
EOF'
else
  echo "Mosquitto configuration for Ethernet already exists in /etc/mosquitto/mosquitto.conf"
fi

echo ">>> Cloning dispenser_hub repository to /home/pi..."
if [ ! -d "/home/pi/dispenser_hub" ]; then
  cd /home/pi
  git clone https://github.com/lucas-iezzi/dispenser_hub.git
else
  echo "Repository already cloned. Pulling latest changes..."
  cd /home/pi/dispenser_hub
  git pull
fi

echo ">>> Creating boot_update.sh script..."
cat <<'EOF' > /home/pi/boot_update.sh
#!/bin/bash

LOG="/home/engineering/boot_update.log"
echo "Boot update started at $(date)" >> $LOG

# Activate the Python virtual environment
echo "Activating Python virtual environment..." >> $LOG
source /home/engineering/venv/bin/activate

# Wait for a usable Wi-Fi IP address
MAX_WAIT=60
ELAPSED=0
while true; do
  WIFI_IP=$(hostname -I | awk '{print $1}')
  if [[ $WIFI_IP != 169.254.* && $WIFI_IP != "" ]]; then
    echo "Good Wi-Fi IP acquired: $WIFI_IP" >> $LOG
    break
  fi
  if (( ELAPSED >= MAX_WAIT )); then
    echo "Timeout waiting for good Wi-Fi IP. Skipping update." >> $LOG
    exit 1
  fi
  sleep 2
  ((ELAPSED+=2))
done

# Ensure Mosquitto service is active
echo "Checking Mosquitto service status..." >> $LOG
MAX_RETRIES=10
RETRY_COUNT=0
while true; do
  if systemctl is-active --quiet mosquitto; then
    echo "Mosquitto service is active." >> $LOG
    break
  fi
  if (( RETRY_COUNT >= MAX_RETRIES )); then
    echo "Mosquitto service failed to start after $MAX_RETRIES attempts." >> $LOG
    exit 1
  fi
  echo "Mosquitto service is not active. Attempting to start it... (Retry $((RETRY_COUNT + 1))/$MAX_RETRIES)" >> $LOG
  sudo systemctl start mosquitto
  sleep 5
  ((RETRY_COUNT++))
done

# Pull latest updates from GitHub
cd /home/engineering/dispenser_hub || exit 1

# Ensure the origin remote is set correctly
if ! git remote -v | grep -q "https://github.com/lucas-iezzi/dispenser_hub.git"; then
  git remote add origin https://github.com/lucas-iezzi/dispenser_hub.git
fi

git pull >> $LOG 2>&1
echo "Git update completed at $(date)" >> $LOG
EOF

chmod +x /home/pi/boot_update.sh

echo ">>> Creating systemd service for boot_update..."
sudo bash -c 'cat <<EOF > /etc/systemd/system/boot_update.service
[Unit]
Description=Update Dispenser Hub Code After WiFi Connect
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/home/pi/boot_update.sh
User=pi
StandardOutput=journal
StandardError=journal
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF'

echo ">>> Enabling boot_update.service..."
sudo systemctl daemon-reexec
sudo systemctl enable boot_update.service

echo ">>> Setup complete! Rebooting..."
sudo reboot
