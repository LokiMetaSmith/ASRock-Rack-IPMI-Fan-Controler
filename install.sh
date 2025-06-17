#!/bin/bash

# This script installs the IPMI fan control service.
# It must be run with root privileges (e.g., using sudo).

set -e

# --- Check for Root ---
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script as root or with sudo."
  exit 1
fi

echo "--- Installing IPMI Fan Control Service ---"

# --- Define Paths ---
# Standard location for locally installed admin scripts
SCRIPT_DEST="/usr/local/sbin/fan_control.py"
# Standard location for systemd service files
SERVICE_DEST="/etc/systemd/system/ipmi-fan-control.service"
# The Python script in the current directory
SCRIPT_SRC="fan_control.py"
# The service file in the current directory
SERVICE_SRC="ipmi-fan-control.service"

# --- Check if Source Files Exist ---
if [ ! -f "$SCRIPT_SRC" ] || [ ! -f "$SERVICE_SRC" ]; then
    echo "ERROR: Make sure fan_control.py and ipmi-fan-control.service are in the same directory as this script."
    exit 1
fi

# --- Copy Files and Set Permissions ---
echo "Copying script to $SCRIPT_DEST..."
cp "$SCRIPT_SRC" "$SCRIPT_DEST"
chmod 755 "$SCRIPT_DEST"

echo "Copying systemd service file to $SERVICE_DEST..."
cp "$SERVICE_SRC" "$SERVICE_DEST"

# --- Reload systemd ---
echo "Reloading systemd daemon..."
systemctl daemon-reload

echo ""
echo "--- Installation Complete ---"
echo ""
echo "NEXT STEPS:"
echo "1. Your fan speeds are currently set in the local 'config.ini' file."
echo "   Please move this file to '/etc/fan_control.ini' or a location of your choice"
echo "   and update the CONFIG_FILE path in $SCRIPT_DEST."
echo ""
echo "2. Enable the service to start on boot:"
echo "   sudo systemctl enable ipmi-fan-control.service"
echo ""
echo "3. Start the service immediately to test it:"
echo "   sudo systemctl start ipmi-fan-control.service"
echo ""
echo "4. Check the service status to see if it ran correctly:"
echo "   sudo systemctl status ipmi-fan-control.service"
echo "   journalctl -u ipmi-fan-control.service"
echo ""
