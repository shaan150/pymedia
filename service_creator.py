import asyncio
import json
import logging
import socket
import sys

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
    # Display the service types with a number
    for i, service_type in enumerate(ServiceType):
        print(f"{i + 1}. {service_type.name}")

    # Ask user for service type
    while True:
        service_type = input("Enter service type: ")
        # check if the service type is valid number and within the range of the service types
        if service_type.isdigit() and 0 < int(service_type) <= len(ServiceType):
            # get the service type from the enum by the number entered by the user
            service_type = list(ServiceType)[int(service_type) - 1].value
            break

        print(
            "Invalid service type. Must be either 'auth_service', 'media_engine', 'client_service', or 'main_service'")
else:
    service_type = args.service_type
    # Convert the service type to ServiceType enum and ensure it's a valid service type
    try:
        service_type = ServiceType[service_type].value
    except KeyError:
        raise Exception("Invalid Service Type")

# uses socket to get available port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("", 0))
s.listen(1)
service_port = s.getsockname()[1]
s.close()

# After determining the service port
print(f"ServicePort: {service_port}")

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
                    break
                print("Invalid IP")
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
        # Set the event loop policy to SelectorEventLoopPolicy on Windows
        try:
            logging.getLogger("asyncio").setLevel(logging.WARNING)
            logging.getLogger("uvicorn").setLevel(logging.WARNING)
            print(f"http://{socket.gethostname()}:{service_port}")
            uvicorn.run(f"{service_type}:app", host="0.0.0.0", port=service_port, reload=False)
        except Exception as e:
            print(f"Error: {e}")
