from fastapi import Request, requests
import time

def setup():
    validate_connection = False
    MAIN_SERVER_URL = ""

    while not validate_connection:
        MAIN_SERVER_URL = input("Enter the main server url: ")
        start_time = time.time()

        while time.time() - start_time < 15:  # Try for 15 seconds
            try:
                response = requests.get(MAIN_SERVER_URL)
                if response.status_code == 200:
                    print("Connection to the main server was successful.")
                    validate_connection = True
                    break
                else:
                    print("Unable to connect, retrying...")
            except requests.ConnectionError:
                print("Connection failed, retrying...")

            time.sleep(2)  # Wait for 2 seconds before retrying

        if not validate_connection:
            print("Failed to validate the connection within 15 seconds.")
            choice = input("Do you want to try again? (y/n): ")
            if choice.lower() != 'y':
                break

    return MAIN_SERVER_URL

# Modify your FastAPI app to use this setup function
MAIN_SERVER_URL = setup()

# Rest of your FastAPI app code...
