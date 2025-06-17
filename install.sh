#!/bin/bash
#
# IPMI Fan Control Service Installer
# ----------------------------------
# This script installs the fan control script and systemd service.
# It is designed to be run from a cloned Git repository.

set -e

# --- Configuration ---
SCRIPT_NAME="fan_control.py"
SERVICE_NAME="ipmi-fan-control.service"
CONFIG_TEMPLATE="config.ini.example"

# Destination Paths
INSTALL_DIR="/usr/local/sbin"
SERVICE_DIR="/etc/systemd/system"
CONFIG_DIR="/etc/ipmi-fan-control"

# Full paths for destination files
SCRIPT_DEST="${INSTALL_DIR}/${SCRIPT_NAME}"
SERVICE_DEST="${SERVICE_DIR}/${SERVICE_NAME}"
CONFIG_DEST="${CONFIG_DIR}/config.ini"

# --- Sanity Checks ---
if [ "$EUID" -ne 0 ]; then
  echo "ERROR: Please run this script as root or with sudo."
  exit 1
fi

if [ ! -f "$SCRIPT_NAME" ] || [ ! -f "$SERVICE_NAME" ] || [ ! -f "$CONFIG_TEMPLATE" ]; then
    echo "ERROR: Missing required files. Please run this script from the root of the Git repository."
    exit 1
fi

echo "--- Installing/Updating IPMI Fan Control Service ---"

# --- Install Script and Service ---
echo "Copying script to $SCRIPT_DEST..."
cp "$SCRIPT_NAME" "$SCRIPT_DEST"
chmod 755 "$SCRIPT_DEST"

echo "Copying systemd service file to $SERVICE_DEST..."
cp "$SERVICE_NAME" "$SERVICE_DEST"

# --- Handle Configuration File ---
# Create the configuration directory if it doesn't exist.
if [ ! -d "$CONFIG_DIR" ]; then
    echo "Creating configuration directory: $CONFIG_DIR"
    mkdir -p "$CONFIG_DIR"
fi

# Only create the config file from the template if it doesn't already exist.
# This preserves user settings during updates.
if [ ! -f "$CONFIG_DEST" ]; then
    echo "No existing configuration found. Creating new config from template..."
    cp "$CONFIG_TEMPLATE" "$CONFIG_DEST"
    echo "IMPORTANT: Please edit your new configuration file at $CONFIG_DEST"
else
    echo "Existing configuration at $CONFIG_DEST found. Skipping creation."
fi

# --- Finalize ---
echo "Reloading systemd daemon to recognize changes..."
systemctl daemon-reload

echo ""
echo "--- Installation/Update Complete ---"
echo ""
echo "To finish setup (if this is a first-time install):"
echo "1. Edit the configuration: sudo nano $CONFIG_DEST"
echo "2. Enable the service to start on boot: sudo systemctl enable $SERVICE_NAME"
echo "3. Start the service now: sudo systemctl start $SERVICE_NAME"
echo ""
echo "To check status, run: sudo systemctl status $SERVICE_NAME"
echo ""
