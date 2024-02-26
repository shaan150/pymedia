import asyncio
import json
import logging
import os
import socket
import sys

import requests
import uvicorn
import argparse

# Check if a command-line argument for service_type is provided
from classes.enum.ServiceType import ServiceType

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--service_type', help='Service Type')
parser.add_argument('-m', '--main_service_url', help='Main Service URL')
parser.add_argument('-a', '--auto', help='Auto Setup')
parser.add_argument('-sk', '--secret_key', help='Secret Key')
args = parser.parse_args()

can_launch = False
secret_key = None

if args.service_type is None:
    # Display the service types
    print("Please select a service type")
    allowed_numbers = []
    # Display the service types with a number excluding database and file service
    for i, service_type in enumerate(ServiceType):
        if service_type.value != "database_service" and service_type.value != "file_service":
            allowed_numbers.append(i + 1)
            print(f"{i + 1}. {service_type.name}")

    # Ask user for service type
    while True:
        service_type = input("Enter service type: ")
        # check if the service type is valid number and within the range of the service types
        if service_type.isdigit() and 0 < int(service_type) <= len(ServiceType) and int(service_type) in allowed_numbers:
            # get the service type from the enum by the number entered by the user
            service_type = list(ServiceType)[int(service_type) - 1].value
            break

        print(
            "Invalid service type. Must be either 'auth_service', 'client_service', or 'main_service'. "
            "please choose a valid number of the service type")
else:
    service_type = args.service_type
    # Convert the service type to ServiceType enum and ensure it's a valid service type
    try:
        service_type = ServiceType[service_type].value
    except KeyError:
        raise Exception("Invalid Service Type")

# uses socket to get available port
ipaddress = socket.gethostbyname(socket.gethostname())
def is_port_available(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) != 0

service_port = 50000
found_port = False

# Loop until an available port is found or the port exceeds 50010
while not found_port and service_port <= 50010:
    if is_port_available(socket.gethostbyname(socket.gethostname()), service_port):
        found_port = True
        break
    service_port += 1

# If an available port was found, proceed with binding and listening
if found_port:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((socket.gethostbyname(socket.gethostname()), service_port))
        s.listen()
        print(f"Server listening on port {service_port}")
        # You can accept connections here using s.accept() in a loop
else:
    raise Exception("Unable to find an available port within the range 50000 to 50010.")

main_service_url = None

# Attempt to read the existing data from the file
# Define the path to your JSON file
file_path = "service_properties.json"

try:
    with open(file_path, "r") as file:
        data = json.load(file)
except FileNotFoundError:
    # If the file doesn't exist, start with an empty dictionary
    data = {}

if service_type != "main_service":
    if args.main_service_url is None:
        if args.auto is None:
            # ask for main service url
            while True:
                main_service_url = input("Enter main service url: ")
                if main_service_url:
                    # check if the main service url is valid and doesn't have http or https
                    if "http://" in main_service_url or "https://" in main_service_url:
                        print("Invalid URL, please enter a valid URL without http or https")
                    elif main_service_url.count(":") != 1:
                        print("Invalid IP, Please Enter With Port Number: xxx.xxx.xxx.xxx:xxxx or domain:xxxx")
                    else:
                        # check if the main service url is valid by trying to connect to it on it's root
                        try:
                            response = requests.get("http://"+main_service_url)
                            if response.status_code == 200:
                                print("Service is up and responding.")
                                break
                            else:
                                print(f"Service responded with status code: {response.status_code}")
                        except Exception as e:
                            print("Service is down or not responding")
        else:
            raise Exception("Main Service URL is required for auto setup")

        data['secret_key'] = args.secret_key
    else:
        main_service_url = args.main_service_url

    data["main_service_url"] = main_service_url

    # Save the main service url to a file service_properties.json
    # create json data

data[str(service_type)] = service_port

with open("service_properties.json", "w") as file:
    json.dump(data, file)

can_launch = True

if __name__ == "__main__":
    if can_launch:
        try:
            os.environ["DEBUG"] = "False"
            logging.getLogger("asyncio").setLevel(logging.WARNING)
            logging.getLogger("uvicorn").setLevel(logging.WARNING)
            # After determining the service port
            print(f"ServicePort: {service_port}")
            print(f"http://{socket.gethostbyname(socket.gethostname())}:{service_port}")
            s.close()
            uvicorn.run(f"{service_type}:app", host="0.0.0.0", port=service_port, reload=False)
        except Exception as e:
            print(f"Error: {e}")
