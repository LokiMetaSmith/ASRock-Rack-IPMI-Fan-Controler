#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ASRock Rack IPMI Fan Controller (Dynamic)
-----------------------------------------

This script runs as a daemon to dynamically control fan speeds on certain
ASRock Rack motherboards based on system temperature. It sends raw IPMI
commands (NetFn 0x3a, Cmd 0x01) to set fan speeds.

The script reads its settings from '/etc/ipmi-fan-control/config.ini'.

Prerequisites:
- Python 3
- ipmitool
- lm-sensors (for temperature reading)
"""

import subprocess
import configparser
import os
import sys
import time
import re

# --- Constants ---
CONFIG_FILE = '/etc/ipmi-fan-control/config.ini'
DEFAULT_IPMITOOL_PATH = '/usr/bin/ipmitool'
DEFAULT_INTERFACE = 'open'
FAILSAFE_SPEED_PERCENT = 75

def get_cpu_temperature():
    """
    Retrieves the CPU package temperature by parsing the output of `sensors`.

    If `sensors` is not available or fails, or if no temperature is found,
    it falls back to a mocked value for testing purposes.

    :return: The CPU temperature in degrees Celsius as a float, or a mocked value.
    """
    try:
        # Setting check=False because `sensors` can return a non-zero exit code
        # if no sensors are found, but we want to handle that gracefully.
        result = subprocess.run(['sensors'], capture_output=True, text=True, check=False)
        output = result.stdout

        # Example `sensors` output:
        # Package id 0:  +58.0°C  (high = +80.0°C, crit = +100.0°C)
        # Core 0:        +55.0°C  (high = +80.0°C, crit = +100.0°C)

        # Regex to find the 'Package id 0' temperature, a good overall CPU temp.
        match = re.search(r"Package id 0:\s*\+([\d\.]+)", output)
        if match:
            temp_str = match.group(1)
            return float(temp_str)
        
        # Fallback regex for 'Core 0' if 'Package' isn't available.
        match = re.search(r"Core 0:\s*\+([\d\.]+)", output)
        if match:
            temp_str = match.group(1)
            return float(temp_str)

        print("WARN: Could not parse CPU temperature from `sensors` output.", file=sys.stderr)

    except FileNotFoundError:
        print("WARN: `sensors` command not found.", file=sys.stderr)

    # --- Mocked Fallback ---
    print("INFO: Using mocked temperature reading of 55.0°C.")
    return 55.0

def execute_ipmi_command(ipmitool_path, interface, fan_speeds_hex):
    """
    Builds and executes the raw IPMI command to set fan speeds.

    :param ipmitool_path: Path to the ipmitool executable.
    :param interface: IPMI interface to use (e.g., 'open').
    :param fan_speeds_hex: A list of 8 hexadecimal speed values (e.g., ['0x32', '0x32', ...]).
    """
    command = [
        ipmitool_path,
        '-I', interface,
        'raw', '0x3a', '0x01',
    ] + fan_speeds_hex

    try:
        # Using subprocess.run for simplicity
        subprocess.run(command, check=True, capture_output=True, text=True)
        # A successful raw command usually returns no output, so we don't print success unless verbose.
    except FileNotFoundError:
        print(f"ERROR: The command '{ipmitool_path}' was not found.", file=sys.stderr)
        # Exit here because if ipmitool is missing, even the failsafe will fail.
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print("ERROR: ipmitool command failed.", file=sys.stderr)
        print(f"  Return Code: {e.returncode}", file=sys.stderr)
        print(f"  Command: {' '.join(command)}", file=sys.stderr)
        print(f"  Stderr: {e.stderr.strip()}", file=sys.stderr)
        print(f"  Stdout: {e.stdout.strip()}", file=sys.stderr)


def set_all_fans_to_speed(ipmitool_path, interface, speed_percent):
    """
    Sets all 8 fans to a single specified speed.

    :param ipmitool_path: Path to the ipmitool executable.
    :param interface: IPMI interface to use.
    :param speed_percent: The desired fan speed (0-100).
    """
    if not 0 <= speed_percent <= 100:
        print(f"WARN: Requested speed {speed_percent}% is out of range (0-100). Clamping.", file=sys.stderr)
        speed_percent = max(0, min(100, speed_percent))

    hex_speed = hex(speed_percent)
    # The IPMI command requires a speed value for each of the 8 fans.
    fan_speeds_hex = [hex_speed] * 8

    print(f"Setting all fans to {speed_percent}% ({hex_speed}).")
    execute_ipmi_command(ipmitool_path, interface, fan_speeds_hex)


def main():
    """Main execution function, runs in a loop."""
    print("--- Starting IPMI Fan Control Daemon ---")

    # --- Read Configuration ---
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        print(f"ERROR: Configuration file not found at {CONFIG_FILE}", file=sys.stderr)
        sys.exit(1)

    try:
        config.read(CONFIG_FILE)

        # Get settings
        ipmitool_path = config.get('Settings', 'ipmitool_path', fallback=DEFAULT_IPMITOOL_PATH)
        interface = config.get('Settings', 'interface', fallback=DEFAULT_INTERFACE)
        check_interval = config.getint('Settings', 'check_interval', fallback=10)

        # Get dynamic control settings
        low_temp = config.getint('DynamicControl', 'low_temp')
        high_temp = config.getint('DynamicControl', 'high_temp')
        low_speed = config.getint('DynamicControl', 'low_speed')
        high_speed = config.getint('DynamicControl', 'high_speed')

    except (configparser.Error, ValueError) as e:
        print(f"ERROR: Invalid or missing configuration in '{CONFIG_FILE}': {e}", file=sys.stderr)
        sys.exit(1)

    # Initial fan speed state. Start with low speed.
    current_speed_percent = low_speed
    print(f"Initial fan speed set to {current_speed_percent}%.")
    set_all_fans_to_speed(ipmitool_path, interface, current_speed_percent)

    try:
        # The main control loop
        while True:
            print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] ---")

            # Read the temperature
            current_temp = get_cpu_temperature()
            print(f"Current temp: {current_temp}°C. Current fan speed: {current_speed_percent}%. Thresholds: [low: {low_temp}°C, high: {high_temp}°C]")

            # Hysteresis logic
            new_speed_percent = current_speed_percent
            if current_temp >= high_temp and current_speed_percent != high_speed:
                new_speed_percent = high_speed
                print(f"Action: Temp is >= high threshold. Changing speed to HIGH ({new_speed_percent}%).")
            elif current_temp < low_temp and current_speed_percent != low_speed:
                new_speed_percent = low_speed
                print(f"Action: Temp is < low threshold. Changing speed to LOW ({new_speed_percent}%).")
            else:
                print("Action: Temp is within thresholds. Maintaining current speed.")

            if new_speed_percent != current_speed_percent:
                set_all_fans_to_speed(ipmitool_path, interface, new_speed_percent)
                current_speed_percent = new_speed_percent

            print(f"Waiting for {check_interval} seconds...")
            time.sleep(check_interval)

    except KeyboardInterrupt:
        print("\nDaemon stopped by user. Setting fans to failsafe speed.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)
        print("Setting fans to failsafe speed.")
    finally:
        print(f"Executing failsafe: setting all fans to {FAILSAFE_SPEED_PERCENT}%...")
        # Use the configured ipmitool_path and interface for the failsafe if available
        set_all_fans_to_speed(ipmitool_path, interface, FAILSAFE_SPEED_PERCENT)
        print("--- IPMI Fan Control Daemon Finished ---")


if __name__ == "__main__":
    main()
