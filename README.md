How to Run My System
To ensure the successful setup and operation of your distributed system, please follow the updated instructions below. These guidelines will help you initialize the system environment, launch the main service, and start additional services on other machines as needed.

Prerequisites
Specific Python Version
This system requires Python 3.12.2 for its operation. Other versions of Python have not been validated for compatibility and may result in unexpected behavior. Ensure Python 3.12.2 is installed on your machine before proceeding.

IDE Recommendation
While this system has been extensively tested in PyCharm, and its use is recommended for the best experience, it should remain operable from any environment capable of running Python 3.12.2, including various IDEs or the command line.

Setup Instructions
Setting Up the Environment Using requirements.txt
Included with the project is a requirements.txt file, which lists all necessary Python modules and dependencies. Using this file to install dependencies is crucial for avoiding compatibility issues and ensuring the system runs with the correct module versions.

Installing Dependencies
PyCharm Users: PyCharm offers an easy way to install packages from the requirements.txt file through its project settings or right-clicking the file and selecting the appropriate option.

Command-Line Users:

Navigate to the project's root directory.
Install the dependencies using the following command:
On Windows or macOS/Linux: pip install -r requirements.txt
This step ensures that all required Python packages are installed, which is essential for a smooth operation of your system.


Launching the Main Service
Execute service_creator.py within the Python terminal in PyCharm or through your command line. This script provides textual instructions to assist in the setup of each service.

Begin by initiating the main service as instructed by the script. This is a crucial first step, and you must follow the prompts accordingly.
Setting Up Additional Services
With the main service operational, you can execute service_creator.py on additional machines. The script will offer instructions similar to the initial setup, allowing for the configuration and launch of other services required by your system.

Additional Notes
Following the on-screen instructions provided by service_creator.py is crucial for a smooth setup process. This script offers an interactive guide designed to efficiently lead you through the initialization of each system component. By utilizing the requirements.txt file for dependency management, you simplify the setup process, ensuring all necessary Python packages are installed without the need to manage a separate virtual environment. This approach streamlines the preparation of your development and operational environments, making it easier to maintain and update as needed.
