#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ASRock Rack IPMI Fan Controller
-------------------------------

This script sends a raw IPMI command to set the fan speeds on certain
ASRock Rack motherboards that use the 0x3a NetFn for fan control.

It is designed to be run as a systemd service at boot.

The script reads its settings from a 'config.ini' file located in the
same directory. This allows for easy configuration of fan speeds and IPMI
interface settings without modifying the script itself.

Prerequisites:
- Python 3
- ipmitool installed and in the system's PATH
- The necessary IPMI kernel modules loaded if using the 'open' interface
  (e.g., ipmi_devintf, ipmi_si, ipmi_msghandler)
"""

import subprocess
import configparser
import os
import sys

# --- Configuration ---
# The configuration file is expected to be in the same directory as the script.
# This makes it easier to manage when installed.
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, 'config.ini')

def main():
    """Main execution function."""
    print("--- Starting IPMI Fan Control Script ---")

    # --- Read Configuration ---
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        print(f"ERROR: Configuration file not found at {CONFIG_FILE}", file=sys.stderr)
        sys.exit(1)

    try:
        config.read(CONFIG_FILE)
        
        # Get IPMI settings
        ipmitool_path = config.get('Settings', 'ipmitool_path', fallback='/usr/bin/ipmitool')
        interface = config.get('Settings', 'interface', fallback='open')

        # Get the fan speeds. We expect 8 fan values.
        fan_speeds_percent = [
            config.getint('FanSpeeds', f'fan_{i}') for i in range(1, 9)
        ]
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        print(f"ERROR: Configuration error in '{CONFIG_FILE}': {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"ERROR: Invalid number in [FanSpeeds] section of '{CONFIG_FILE}': {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Using IPMI interface: {interface}")
    print(f"Desired fan speeds (%): {fan_speeds_percent}")

    # --- Build IPMI Command ---
    # Base command structure
    command = [
        ipmitool_path,
        '-I', interface,
        'raw', '0x3a', '0x01'
    ]

    # Convert percentage speeds to hex and add to the command
    for speed in fan_speeds_percent:
        if not 0 <= speed <= 100:
            print(f"ERROR: Fan speed {speed}% is out of range. Must be between 0 and 100.", file=sys.stderr)
            sys.exit(1)
        # Convert the integer percentage to a hexadecimal string (e.g., 50 -> "0x32")
        hex_speed = hex(speed)
        command.append(hex_speed)

    print(f"Executing command: {' '.join(command)}")

    # --- Execute Command ---
    try:
        # Run the command. check=True will raise an exception if the command fails.
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("SUCCESS: IPMI command sent successfully.")
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")

    except FileNotFoundError:
        print(f"ERROR: The command '{ipmitool_path}' was not found.", file=sys.stderr)
        print("Please ensure 'ipmitool' is installed and the path in config.ini is correct.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        # This block catches errors from ipmitool itself (e.g., 'Invalid command')
        print("ERROR: ipmitool command failed.", file=sys.stderr)
        print(f"Return Code: {e.returncode}", file=sys.stderr)
        print(f"Stderr: {e.stderr.strip()}", file=sys.stderr)
        print(f"Stdout: {e.stdout.strip()}", file=sys.stderr)
        print("Troubleshooting: Is the IPMI interface correct? Are kernel modules loaded for '-I open'?", file=sys.stderr)
        sys.exit(1)

    print("--- IPMI Fan Control Script Finished ---")

if __name__ == "__main__":
    main()
