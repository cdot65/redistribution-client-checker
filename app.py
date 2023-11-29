# standard library imports
import argparse
import logging
import re
import xml.etree.ElementTree as ET


# 3rd party imports
import xmltodict
from netmiko import ConnectHandler
from tabulate import tabulate
from panos.errors import PanDeviceError
from panos.firewall import Firewall
from panos.panorama import Panorama
from config import settings

# Set up argument parser
parser = argparse.ArgumentParser(
    description="Script to interact with Panorama appliance."
)
parser.add_argument(
    "--debug",
    action="store_true",
    help="Enable debug logging",
)
parser.add_argument(
    "--hostname",
    default=settings["panorama"]["hostname"],
    help="Hostname of the Panorama appliance",
)
parser.add_argument(
    "--username",
    default=settings["panorama"]["username"],
    help="Username for the Panorama appliance",
)
parser.add_argument(
    "--password",
    default=settings["panorama"]["password"],
    help="Password for the Panorama appliance",
)
args = parser.parse_args()


# Configure logging
if args.debug:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)


def connect_to_panorama(host, username, password):
    panorama_device = {
        "device_type": "paloalto_panos",
        "host": host,
        "username": username,
        "password": password,
        "port": 22,
    }

    try:
        net_connect = ConnectHandler(**panorama_device)
        logging.debug("Connected successfully to the device.")
        return net_connect

    except Exception as e:
        logging.error(f"Error connecting to the device: {e}")
        return None


def send_command_to_panorama(net_connect, command):
    try:
        logging.debug(f"Sending command: {command}")
        output = net_connect.send_command(command, expect_string=r">")
        logging.debug("Command executed.")
        return output

    except Exception as e:
        logging.error(f"Error sending command: {e}")
        return None


def parse_status_command_output(output):
    # Regex patterns for different lines
    patterns = {
        "redistribution_status": r"Redistribution service:\s+(?P<status>\w+)",
        "ssl_config": r"SSL config:\s+(?P<ssl_config>.+)",
        "number_of_clients": r"number of clients:\s+(?P<clients>\d+)",
    }

    # Parsing and extracting data
    parsed_data = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, output)
        if match:
            parsed_data[key] = match.group(1)

    # Specific transformations for certain fields
    if "ssl_config" in parsed_data:
        parsed_data["ssl_config"] = (
            parsed_data["ssl_config"].lower().replace(" ", "_")
        )  # e.g., "Default certificates" to "default_certs"

    if "number_of_clients" in parsed_data:
        parsed_data["number_of_clients"] = int(parsed_data["number_of_clients"])

    return parsed_data


def parse_xml_response(response):
    """Converts XML response to a dictionary."""
    result_xml = ET.tostring(response, encoding="utf-8").decode("utf-8")
    return xmltodict.parse(result_xml)


if __name__ == "__main__":
    # Netmiko work
    net_connect = connect_to_panorama(
        args.hostname,
        args.username,
        args.password,
    )

    # show redistribution service status
    if net_connect:
        # using netmiko because the XML is missing the ssl config
        show_redistribution_service_status = send_command_to_panorama(
            net_connect,
            "show redistribution service status",
        )
        if show_redistribution_service_status:
            logging.debug("Command output:")
            logging.debug(show_redistribution_service_status)
            parsed_output = parse_status_command_output(
                show_redistribution_service_status
            )
            logging.debug(parsed_output)
        else:
            logging.debug("No output received from the command.")

        net_connect.disconnect()
    else:
        logging.error("Unable to establish connection with the device.")

    # check to see if redistribution_status is equal to `up`` and ssl_config is NOT `default_certificates`
    if (
        parsed_output["redistribution_status"] == "up"
        and parsed_output["ssl_config"] == "default_certificates"
    ):
        # create a panorama object
        pan = Panorama(
            args.hostname,
            args.username,
            args.password,
        )

        # validate creds
        try:
            pan.refresh_system_info()
            logging.debug("Successfully connected to Panorama with credientials")
        except PanDeviceError as pan_device_error:
            logging.error(f"Failed to connect to Panorama: {pan_device_error}")

        # first API call to retreive all redistribution clients
        redist_clients = pan.op(
            cmd="<show><redistribution><service><client>all</client></service></redistribution></show>",
            cmd_xml=False,
        )

        # flip to python dict
        list_of_redist_clients = parse_xml_response(redist_clients)
        logging.debug(f"list_of_redist_clients: {list_of_redist_clients}")

        # check to see if the response returns a single entry or a list of entries
        if isinstance(list_of_redist_clients["response"]["result"]["entry"], dict):
            firewall = Firewall(
                serial=list_of_redist_clients["response"]["result"]["entry"]["host"]
            )
            pan.add(firewall)
        else:
            for each in list_of_redist_clients["response"]["result"]["entry"]:
                firewall = Firewall(serial=each["host"])
                pan.add(firewall)

        # debug
        logging.debug(pan.children)

        # second API call to retreive all connected devices
        # this will only return actively connected devices
        show_devices_connected = pan.op(
            cmd="<show><devices><connected/></devices></show>", cmd_xml=False
        )
        list_of_connected_devices = parse_xml_response(show_devices_connected)
        # logging.debug(f"list_of_connected_devices: {list_of_connected_devices}")

        redis_client_list = []

        for firewall in pan.children:
            show_redistribution_client_all = firewall.op(
                cmd="<show><redistribution><service><client>all</client></service></redistribution></show>",
                cmd_xml=False,
            )
            redist_client_firewall_info = parse_xml_response(
                show_redistribution_client_all
            )
            logging.debug(redist_client_firewall_info)

            show_system_info = firewall.op(
                cmd="<show><system><info/></system></show>", cmd_xml=False
            )
            system_info = parse_xml_response(show_system_info)
            fw_info = system_info["response"]["result"]["system"]
            fw = {
                "hostname": fw_info["hostname"],
                "ipaddress": fw_info["ip-address"],
                "serial": fw_info["serial"],
                "model": fw_info["model"],
                "sw_version": fw_info["sw-version"],
                "app_version": fw_info["app-version"],
                "device_cert_status": fw_info["device-certificate-status"],
            }
            # Check if redist_client_firewall_info["response"]["result"] is None
            is_redistribution_server = (
                redist_client_firewall_info["response"]["result"] is not None
            )

            # Add the new key/value pair to the fw dictionary
            fw["redistr_server"] = is_redistribution_server

            redis_client_list.append(fw)

        # Extract headers from the first dictionary in the list
        headers = list(redis_client_list[0].keys()) if redis_client_list else []

        # Convert dictionaries to lists of values
        table_data = [list(item.values()) for item in redis_client_list]

        # Use tabulate to create a table
        table = tabulate(table_data, headers, tablefmt="grid")

        print(table)
