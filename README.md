# Panorama Interaction Script

## Description

This Python script is designed to interact with the Panorama appliance, a centralized security management system for Palo Alto Networks' firewalls. It leverages the Panorama API and other tools to execute various network security-related tasks, such as checking redistribution service status, retrieving client information, and gathering system details from connected devices.

## Features

- Connect to a Panorama appliance using Netmiko.
- Send commands to Panorama and parse the output.
- Work with PAN-OS API through the panos module for advanced tasks.
- Generate a detailed table of connected devices and their status.

## Requirements

- Python 3.x
- Netmiko
- xmltodict
- tabulate
- pan-python (for the panos module)

## Installation

Ensure Python 3.x is installed on your system.

Install the required Python packages:

```bash
pip install -r requirements.txt
```

```bash
pip install netmiko xmltodict tabulate pan-python dynaconf
```

Clone this repository or download the script to your local machine.

## Configuration

Before running the script, configure the config.py file with the appropriate settings for your Panorama appliance, including hostname, username, and password.

Usage

Run the script with the following command, optionally specifying parameters for hostname, username, password, and debug mode:

```bash
python panorama_script.py --hostname [hostname] --username [username] --password [password] --debug
```

## Script Functions

The script can perform the following functions:

- `connect_to_panorama`: Establishes a connection to the Panorama appliance.
- `send_command_to_panorama`: Sends CLI commands to the Panorama appliance.
- `parse_status_command_output`: Parses the output of the status command.
- `parse_xml_response`: Converts XML responses to Python dictionaries.

### Debugging

Enable debug mode using the --debug flag to view detailed logging for troubleshooting.

## Contributions

Contributions to this script are welcome. Please ensure to follow best practices for code style and include comments where necessary.

## License

This script is released under the MIT License. See the LICENSE file for more details.

## Contact

For any inquiries or issues, please open an issue in the repository or contact the maintainer directly.
