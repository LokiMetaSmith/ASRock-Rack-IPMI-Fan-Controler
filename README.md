# ASRock Rack IPMI Fan Controller

A simple and robust solution to control fan speeds on certain ASRock Rack server motherboards via IPMI, designed to run automatically at boot.

## Features

-   Sets custom fan speeds using raw IPMI commands.
-   Configuration is managed in a simple `.ini` file, separate from the code.
-   Installs as a `systemd` service for reliable execution on boot.
-   Installation script for easy setup and updates.

## Prerequisites

-   A Linux server with `systemd`.
-   `python3` installed.
-   `git` installed.
-   `ipmitool` installed (`sudo apt install ipmitool`).
-   Root or `sudo` privileges.

## Installation

1.  **Clone the Repository**
    Clone this repository to your server, for example in your home directory.
    ```bash
    git clone https://your-git-repo-url/fan-control.git
    cd fan-control
    ```

2.  **Run the Installer**
    The installer script will copy the necessary files to system locations and set permissions.
    ```bash
    sudo ./install.sh
    ```

## Configuration

After installation, a new configuration file will be created at `/etc/ipmi-fan-control/config.ini` (if it didn't already exist).

1.  **Edit the Configuration File:**
    Open the file with a text editor to set your desired fan speeds and IPMI interface.
    ```bash
    sudo nano /etc/ipmi-fan-control/config.ini
    ```

2.  **Configure `[Settings]`:**
    -   `interface`: Use `open` for local access (recommended) or `lanplus` for network access.

3.  **Configure `[FanSpeeds]`:**
    -   Set `fan_1` through `fan_8` to your desired percentage (0-100).

## Service Management

Once configured, you can manage the service using standard `systemctl` commands.

-   **Enable the service (to start on boot):**
    ```bash
    sudo systemctl enable ipmi-fan-control.service
    ```

-   **Start the service immediately:**
    ```bash
    sudo systemctl start ipmi-fan-control.service
    ```

-   **Check the service status:**
    ```bash
    sudo systemctl status ipmi-fan-control.service
    ```

-   **View service logs:**
    ```bash
    journalctl -u ipmi-fan-control.service
    ```

-   **Restart the service (after changing config):**
    ```bash
    sudo systemctl restart ipmi-fan-control.service
    ```

## Updating the Script

To update to the latest version from your Git repository:

1.  Navigate to your cloned repository directory.
    ```bash
    cd ~/fan-control
    ```
2.  Pull the latest changes.
    ```bash
    git pull
    ```
3.  Re-run the installer to copy the new files. Your configuration file will be preserved.
    ```bash
    sudo ./install.sh
    ```
4.  Restart the service to apply the new script.
    ```bash
    sudo systemctl restart ipmi-fan-control.service
    ```
