#!/bin/bash

set -e

echo ">>> Updating and installing system dependencies..."
sudo apt update
sudo apt install -y git dnsmasq mosquitto mosquitto-clients python3-pip

echo ">>> Creating Python virtual environment..."
VENV_PATH="/home/pi/dispenser_venv"
if [ ! -d "$VENV_PATH" ]; then
  python3 -m venv "$VENV_PATH"
fi

echo ">>> Installing Python dependencies into virtual environment..."
source "$VENV_PATH/bin/activate"
pip install --upgrade pip
pip install paho-mqtt pydantic
deactivate

echo ">>> Enabling services to start on boot..."
sudo systemctl enable dnsmasq
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

echo ">>> Configuring static IP on eth0 using NetworkManager..."
ETH_CONN=$(nmcli -t -f NAME,DEVICE con show --active | grep ':eth0' | cut -d: -f1)

if [ -z "$ETH_CONN" ]; then
  echo "No active Ethernet connection found. Creating one..."
  sudo nmcli con add type ethernet ifname eth0 con-name eth0-static
  ETH_CONN="eth0-static"
fi

# Configure static IP
sudo nmcli con modify "$ETH_CONN" ipv4.addresses 192.168.4.1/24
sudo nmcli con modify "$ETH_CONN" ipv4.method manual
sudo nmcli con modify "$ETH_CONN" connection.autoconnect yes

# Bring connection up
sudo nmcli con up "$ETH_CONN"


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

echo ">>> Creating boot_update.sh script..."
cat <<'EOF' > /home/pi/boot_update.sh
#!/bin/bash

LOG="/home/pi/boot_update.log"
echo "Boot update started at $(date)" >> $LOG

# Activate virtual environment
source /home/pi/dispenser_venv/bin/activate

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
    break  # Allow the system to continue booting
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
    echo "Mosquitto service failed to start after $MAX_RETRIES attempts. Continuing boot process." >> $LOG
    break  # Allow the system to continue booting
  fi
  echo "Mosquitto service is not active. Attempting to start it... (Retry $((RETRY_COUNT + 1))/$MAX_RETRIES)" >> $LOG
  sudo systemctl start mosquitto
  sleep 5
  ((RETRY_COUNT++))
done

# Delete and clone fresh copy of dispenser_hub
echo "Refreshing GitHub repo..." >> $LOG
rm -rf /home/pi/dispenser_hub
if git clone https://github.com/lucas-iezzi/dispenser_hub.git /home/pi/dispenser_hub >> $LOG 2>&1; then
  echo "Cloned latest code at $(date)" >> $LOG
else
  echo "Failed to clone repository." >> $LOG
fi
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

echo ">>> Adding virtual environment activation to .bashrc..."
if ! grep -q "source /home/pi/dispenser_venv/bin/activate" /home/pi/.bashrc; then
  echo "source /home/pi/dispenser_venv/bin/activate" >> /home/pi/.bashrc
fi

echo ">>> Enabling boot_update.service..."
sudo systemctl daemon-reexec
sudo systemctl enable boot_update.service

echo ">>> Setup complete! Rebooting..."
sudo reboot
