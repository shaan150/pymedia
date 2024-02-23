import asyncio
import secrets
import time
from datetime import datetime
from time import time
from typing import Dict, List

from fastapi import HTTPException, Request
from fastapi.logger import logger
from httpx import HTTPStatusError

from classes.ServiceInfo import ServiceInfo
from classes.enum.ServiceType import ServiceType
from classes.exception.FailedServiceCreationException import FailedServiceCreationException
from classes.exception.InvalidServiceException import InvalidServiceException
from classes.exception.NoAvailableServicesException import NoAvailableServicesException
from classes.services.BaseService import BaseService
from utils.service_utils import handle_rest_request, start_service


class MainService(BaseService):
    """

    MainService Class
    ================

    This class represents the main service of the application. It extends the `BaseService` class.

    Attributes:
    -----------
    - `services` (Dict[str, ServiceInfo]): A dictionary that stores the services associated with the MainService instance.
    - `secret_key` (str): A secret key generated using the `secrets` module.

    Methods:
    --------
    - `start_background_tasks()`: Start background tasks for the service.
    - `stop()`: Stops the services.
    - `setup_services()`: Set up the required services.
    - `setup_service(service_type: ServiceType)`: Set up a specific service.
    - `check_services()`: Check services periodically and perform necessary checks.
    - `perform_service_check(service)`: Check the status of a service and perform necessary actions based on the result.
    - `handle_service_failure(service: ServiceInfo)`: Handle a service failure by finding a replacement and deleting the failed service.
    - `verify_ip(request: Request)`: Verify if the client IP in the request is allowed to access the service.
    - `update_or_add_service(service: ServiceInfo)`: Update or add a service to the system.
    - `del_service(url: str)`: Remove a service from the collection.
    """
    def __init__(self):
        super().__init__(ServiceType.MAIN_SERVICE)
        self.services: Dict[str, ServiceInfo] = {}
        self.secret_key = secrets.token_hex(32)



    async def start_background_tasks(self):
        """
        Start background tasks for the service.

        :return: None
        """
        await super().start_background_tasks()
        logger.info(f"Starting background tasks for {self.service_name}")
        setup_services_task = asyncio.create_task(self.setup_services())
        self.tasks.append(setup_services_task)
        update_task = asyncio.create_task(self.check_services())
        self.tasks.append(update_task)

    async def stop(self):
        """
        Stops the services.

        :return: None
        """
        await super().stop()

        services_to_stop: List[ServiceInfo] = []

        async with self.services_lock:
            if self.services:
                services_to_stop = list(self.services.values())

        # tell all services to stop

        if services_to_stop:
            for service in services_to_stop:
                response = await self.service_exception_handling(service.url, "stop", "POST")
                if response.status_code != 200:
                    logger.error(f"Failed to stop service {service.name}")
                else:
                    logger.info(f"Service {service.name} stopped")

    async def setup_services(self):
        """
        Set up the required services.

        :return: None
        """
        try:
            await self.setup_service(ServiceType.DATABASE_SERVICE)
            await self.setup_service(ServiceType.FILE_SERVICE)
            await self.setup_service(ServiceType.AUTH_SERVICE)
            await asyncio.sleep(5)
            await self.setup_service(ServiceType.CLIENT_SERVICE)

        except Exception as e:
            logger.error(f"Error in setup_services: {str(e)}")

    async def setup_service(self, service_type: ServiceType):
        """
        :param service_type: The type of service to be set up.
        :type service_type: ServiceType
        :raises FailedServiceCreationException: If failed to start the service.
        :raises NoAvailableServicesException: If no services of the given type are available.
        :return: None
        :rtype: None
        """
        async with self.services_lock:
            service = [service for service in self.services.values() if service.type == service_type.name]
            logger.info(service)

        if service is None or len(service) == 0:
            try:
                await start_service(self.service_url, service_type)
                service = await self.wait_for_service(service_type, [])
            except Exception as e:
                logger.error(f"Failed to start service of type {service_type.name}: {e}")
                raise FailedServiceCreationException(f"Failed to start service of type {service_type.name}: {e}")

        if service is None:
            raise NoAvailableServicesException(f"Unable to setup {service_type.name}")

    async def check_services(self):
        """
        Check the services and perform necessary checks for each service that has exceeded the timeout.

        :return: None
        """
        while True:
            services_to_check: List = []

            # Minimize time lock is held
            async with self.services_lock:
                if self.services:
                    # Copy necessary info to reduce lock holding time
                    services_to_check = [(service, datetime.now() - service.last_update) for service in self.services.values()]

            # Process services outside of lock context to allow other operations to proceed
            check_tasks = []
            for service, time_diff in services_to_check:
                if time_diff.total_seconds() > 60:  # 1 minute timeout
                    check_tasks.append(self.perform_service_check(service))
                    print("Service to check: ", service.name, time_diff.total_seconds())

            if check_tasks:
                await asyncio.gather(*check_tasks)

            await asyncio.sleep(100)  # Wait for 5 minutes before next check

    async def perform_service_check(self, service):
        """
        Check the status of a service and perform necessary actions based on the result.

        :param service: A service object to be checked.
        :return: None

        """
        conn_success = await self.check_and_update_service(service)
        if not conn_success:
            await self.handle_service_failure(service)
        else:
            logger.info(f"Service {service.name} online. Checking load...")
            service.last_update = time()
            try:
                await self.get_optimal_service_instance(service.type)
            except NoAvailableServicesException as e:
                logger.error(f"No available services to start: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Error in get_optimal_service_instance: {str(e)}")
                raise ValueError(f"Error Handling Endpoint: {str(e)}")

    async def handle_service_failure(self, service: ServiceInfo):
        """
        Handle a service failure by finding a replacement and deleting the failed service.

        :param service: The ServiceInfo object representing the failed service.
        :return: None
        :raises: NoAvailableServicesException if no replacement service is found.
                 FailedServiceCreationException if there is an issue starting a new instance of the service.
                 FailedServiceCreationException for any other unexpected errors.
        """
        logger.info(f"Service {service.name} offline. Attempting to find a replacement...")

        try:
            optimal_service = await self.get_optimal_service_instance(service.type)
            if not optimal_service:  # If no replacement service is found, raise an exception
                logger.error(f"No replacement available for service {service.name} of type {service.type}.")
                raise NoAvailableServicesException(f"No replacement available for service {service.type}.")

            # Proceed to delete the failed service only if a replacement has been successfully found
            await self.del_service(service.url)
            logger.info(f"Successfully replaced service {service.name}.")

        except NoAvailableServicesException as e:
            # Specific exception handling for no available services
            logger.error(f"No available services to start for type {service.type}: {e}")
            raise  # Reraise the exception to be handled further up if necessary

        except FailedServiceCreationException as e:
            # Handle failed service creation specifically if needed
            logger.error(f"Failed to start a new instance of {service.type}: {e}")
            raise

        except Exception as e:  # Consider catching more specific exceptions as needed
            logger.error(f"Unexpected error handling failure of service {service.name}: {e}")
            raise FailedServiceCreationException(f"Unexpected error during service failure handling: {e}")

    async def verify_ip(self, request: Request):
        """
        Verify if the client IP in the request is allowed to access the service.

        :param request: The request object that contains the client IP.
        :type request: Request
        :raises HTTPException: If the client IP is not allowed to access the service.
        """
        client_ip = request.client.host

        async with self.services_lock:
            allowed_ips = []
            for service in self.services.values():
                ip_address = await service.extract_ip_from_url()
                if ip_address is not None:
                    allowed_ips.append(ip_address)

        if client_ip not in allowed_ips:
            raise HTTPException(status_code=403, detail="Access forbidden")

    async def update_or_add_service(self, service: ServiceInfo):
        """
        Update or add a service to the system.

        :param service: The ServiceInfo object representing the service to be updated or added.
        :type service: ServiceInfo
        :return: None
        :raises InvalidServiceException: If the service is None.
        :raises TypeError: If the service is not of type ServiceInfo.
        """
        if service is None:
            raise InvalidServiceException()

        if not isinstance(service, ServiceInfo):
            raise TypeError(f"Invalid type for service. Expected ServiceInfo, got {type(service).__name__}.")

        created = None
        async with self.services_lock:
            action = "updated" if service.url in self.services else "added"
            try:
                if service.url in self.services:
                    created = self.services[service.url].creation_time

                self.services[service.url] = service
                if created:
                    self.services[service.url].creation_time = created
                else:
                    self.services[service.url].creation_time = time()

                logger.info(f"Service {service.name} {action}.")
            except Exception as e:
                raise

    async def del_service(self, url: str):
        """
        Remove a service from the collection.

        :param url: The URL of the service to be removed.
        :type url: str
        :raise InvalidServiceException: If the URL is None.
        :raise TypeError: If the URL is not of type str.
        :raise ValueError: If the service is not found.
        """
        if url is None:
            raise InvalidServiceException("Invalid Service URL. Cannot be None.")

        if not isinstance(url, str):
            raise TypeError(f"Invalid type for url. Expected str, got {type(url).__name__}.")

        async with self.services_lock:
            # get the service from the list
            try:
                service = self.services[url]
                del self.services[url]
                logger.info(f"Service {service.name} removed.")
            except KeyError:
                error_message = f"Service {url} not found."
                logger.error(error_message)
                raise ValueError(error_message)

    async def get_service(self, service_type: ServiceType):
        """
        Retrieve the optimal service instance for the given service type.

        :param service_type: The type of service to retrieve. Must be an instance of ServiceType.
        :return: The optimal service instance for the given service type.

        :raise InvalidServiceException: If the service_type parameter is None.
        :raise TypeError: If the service_type parameter is not of type ServiceType.
        :raise NoAvailableServicesException: If no available services are found for the given service type.
        :raise TimeoutError: If a timeout occurs while waiting for the service.
        :raise ValueError: If an unexpected error occurs while retrieving the service.
        """
        if service_type is None:
            raise InvalidServiceException("Service type cannot be None.")

        if not isinstance(service_type, ServiceType):
            raise TypeError(f"Invalid type for service_type. Expected ServiceType, got {type(service_type).__name__}.")

        logger.info(f"Attempting to retrieve optimal service instance for: {service_type.name}")

        if service_type is ServiceType.FILE_SERVICE or service_type is ServiceType.DATABASE_SERVICE:
            service = next((service for service in self.services.values() if service.type == service_type.name), None)
            if service:
                # check if the service is online
                return service
            else:
                # if the service is not available, start a new instance
                return await self.create_new_instance(service_type)

        try:
            optimal_service = await self.get_optimal_service_instance(service_type)
            if optimal_service:
                # Assuming optimal_service provides a URL or some identifier; adjust based on your implementation
                logger.info(
                    f"Optimal service instance retrieved: {optimal_service} for service type {service_type.name}")
                return {"url": optimal_service}
            else:
                # It might be more appropriate to log this case and return a specific response or raise an exception
                logger.warning(f"No available services found for {service_type.name}.")
                raise NoAvailableServicesException(f"No available services found for {service_type.name}.")
        except NoAvailableServicesException as e:
            logger.error(f"No available services exception: {e}")
            raise
        except TimeoutError as e:
            logger.error(f"Timeout occurred while waiting for service {service_type.name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error encountered in get_service for {service_type.name}: {e}")
            raise ValueError(f"Unexpected error while retrieving service: {e}")

    async def get_optimal_service_instance(self, service_type: ServiceType, timeout: int = 100,
                                           retry_interval: int = 5):
        """
        :param service_type: The type of service to find an optimal instance for.
        :param timeout: The maximum time in seconds to wait for an optimal service instance. Default is 100 seconds.
        :param retry_interval: The time in seconds to wait before retrying to find an optimal service instance. Default is 5 seconds.
        :return: The optimal service instance if found, otherwise None.

        This method asynchronously retrieves an optimal service instance of the specified type. It searches for the optimal service by repeatedly calling the `select_optimal_service` method
        * until a suitable instance is found. The search process continues until either a suitable instance is found or the timeout value is reached.

        If a suitable service instance is found, it is returned. If no suitable instance is found within the specified timeout, this method logs a warning message and returns None.
        """
        if service_type is None:
            raise InvalidServiceException("Service type cannot be None.")

        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            optimal_service = await self.select_optimal_service(service_type)
            if optimal_service:
                # Optimal service found, returning its information
                return optimal_service

            # Wait before retrying to reduce load and give time for the state to change
            await asyncio.sleep(retry_interval)

        # If no services are found after the timeout, log this event and return None
        logger.warning(f"No optimal service instance found for {service_type} after {timeout} seconds.")
        return None

    async def select_optimal_service(self, service_type: ServiceType):
        """
        :param service_type: The type of service being selected.
        :return: The URL of the optimal service.

        This method selects the optimal service of a given type. It calculates the scores of all existing services of the given type and selects the service with the highest score.

        If no services of the given type exist, a new instance of that type is created.

        If the scores of all existing services are above 0.07, a new instance of the given type is created.

        The URL of the optimal service is returned.
        """
        if service_type is None:
            raise InvalidServiceException("Service type cannot be None.")

        if not isinstance(service_type, ServiceType):
            raise TypeError(f"Invalid type for service_type. Expected ServiceType, got {type(service_type).__name__}.")

        need_new_service = False

        async with self.services_lock:  # Acquire the lock
            # Early return if no services are registered
            if not self.services or not any(service.type == service_type.name for service in self.services.values()):
                need_new_service = True

        if need_new_service:
            return await self.create_new_instance(service_type, False)

        async with self.services_lock:  # Acquire the lock
            coroutines = [service.calc_score() for service in self.services.values() if
                          service.type == service_type.name]

        scores = await asyncio.gather(*coroutines)
        # Re-acquire the lock for accessing self.services again
        async with self.services_lock:
            # Condition to decide if a new service is needed
            if not scores or min(scores) > 0.07:
                need_new_service = True

        if need_new_service:
            return await self.create_new_instance(service_type)

        async with self.services_lock:
            score_service_pairs = list(zip(scores, [s for s in self.services.values() if s.type == service_type.name]))

        optimal_service = max(score_service_pairs, key=lambda pair: pair[0])[1]

        return optimal_service.url

    async def wait_for_service(self, service_type: ServiceType, current_services):
        """
        :param service_type: The type of service to wait for.
        :param current_services: The list of current services.

        :return: The new service of the specified type that became operational, or None if a timeout occurred.

        This method waits for a new service of the specified type to become operational. It compares the count of updated services against the count of current services to detect the addition
        * of new services. If a new service is found, the method returns the new service. If a timeout occurs, the method returns None.

        If the service_type parameter is not of type ServiceType, a TypeError is raised.

        The method uses an exponential backoff or a fixed delay for retries, waiting 1 second between each retry. The total timeout is set to 150 seconds (5 intervals of 30 seconds). The timeout
        * scenario is logged and handled with an error message.
        """
        if not isinstance(service_type, ServiceType):
            raise TypeError(f"Invalid type for service_type. Expected ServiceType, got {type(service_type).__name__}.")

        logger.info(f"Waiting for new service of type {service_type.name} to become operational...")

        start_time = asyncio.get_event_loop().time()
        timeout = 30 * 5  # 5 intervals of 30 seconds
        while asyncio.get_event_loop().time() - start_time < timeout:
            async with self.services_lock:
                # Ensure thread-safe access to self.services
                updated_services = [service for service in self.services.values() if service.type == service_type.name]

            # Check for the addition of new services by comparing the count against the snapshot
            if len(updated_services) > len(current_services):
                # Assuming the new service is the one added last; adjust as needed
                new_service = max(updated_services, key=lambda s: s.creation_time)
                logger.info(f"New service of type {service_type.name} is now operational: {new_service.name}.")
                return new_service

            # Use an exponential backoff or a fixed delay for retries to minimize resource usage
            await asyncio.sleep(1)  # Consider adjusting this based on your application's needs

        # Log and handle the timeout scenario
        logger.error(f"Timeout waiting for a new service of type {service_type.name} to become operational.")
        return None

    async def create_new_instance(self, service_type: ServiceType, existing_services=True):
        """
        :param service_type: The type of service to create a new instance of.
        :param existing_services: A boolean flag indicating whether to use existing services or not. Default is True.
        :return: The newly created service instance.

        This method is used to create a new instance of a service. It takes the service type as a parameter and optionally, a flag indicating whether to use existing services or not. If existing
        *_services is True, it will select the optimal service based on their scores and start a new service instance, if required. If existing_services is False, it will start a new service
        * instance regardless of the existing services.

        The method first validates the input parameters to ensure that service_type is of type ServiceType. If it is not, a TypeError is raised.

        Then, it logs the intention to create a new service instance for clarity and debugging purposes.

        Next, it starts a new service instance asynchronously by calling the start_service method. If existing_services is True, it calculates scores for available services and selects the optimal
        * service based on the highest score. It then sends a request to start the selected optimal service.

        After starting the new service, it waits for the service to become available and operational by calling the wait_for_service method. If the new service does not become operational within
        * the expected timeframe, an Exception is raised.

        Finally, it logs the successful creation and registration of the new service instance and returns the newly created service.

        If any exception occurs during the process, it logs the failure and raises a FailedServiceCreationException with an error message.
        """
        # Validate input parameters for type correctness
        if not isinstance(service_type, ServiceType):
            raise TypeError(f"Invalid type for service_type. Expected ServiceType, got {type(service_type).__name__}.")

        # Log the intention to create a new service instance for clarity and debugging
        logger.info(f"Attempting to create a new instance of service type: {service_type.name}.")

        # Asynchronously start a new service instance
        try:
            current_services = []

            if not existing_services:
                await start_service(self.service_url, service_type)

            else:
                async with self.services_lock:
                    current_services = [service for service in self.services.values() if
                                        service.type == service_type.name]

                    # Calculate scores for available services to determine if a new instance is needed
                    coroutines = [service.calc_available_score() for service in self.services.values() if
                                  service.type == service_type]

                scores = await asyncio.gather(*coroutines)
                # If existing services are sufficient, select the optimal service

                async with self.services_lock:
                    score_service_pairs = list(
                        zip(scores, [s for s in self.services.values() if s.type == service_type.name]))

                optimal_service = max(score_service_pairs, key=lambda pair: pair[0])[1]

                optimal_service_url = optimal_service.url

                await handle_rest_request(optimal_service_url, "start_service", "POST",
                                          data={"service_type": service_type.value})

            # Wait for the new service to become available and operational
            new_service = await self.wait_for_service(service_type, current_services)

            if not new_service:
                raise Exception("New service did not become operational within expected timeframe.")

            logger.info(f"Successfully created and registered new service instance: {new_service.name}.")
            return new_service
        except Exception as e:
            logger.error(f"Failed to create a new instance of {service_type.name}: {e}")
            raise FailedServiceCreationException(f"Failed to create a new instance of {service_type.name}: {e}")

    async def check_and_update_service(self, service):
        """
        :param service: An instance of the Service class representing the service to be checked and updated.
        :return: A boolean value indicating whether the service was successfully checked and updated.

        This method is used to check the availability of a service by performing a GET request to the service root using the
        `service_exception_handling` method. If the response status code is 200, it indicates that the service is online, and
        the method logs the success message and updates the `last_update` attribute of the service with the current time.
        If an `HTTPStatusError` exception is raised, the method logs an error message containing the service name, the
        response status code, and the error message. Finally, if any exception occurs during the process, the method returns
        False.

        Example usage:
        ```python
        service = Service(...)
        result = await check_and_update_service(service)
        if result:
            print("Service checked and updated successfully.")
        else:
            print("Failed to check and update service.")
        ```
        """
        try:
            # Using handle_rest_request to perform a GET request to the service root
            response = await self.service_exception_handling(service.url, "", "GET")

            if response.status_code == 200:
                logger.info(f"Service {service.name} online.")
                service.last_update = time()
                return True

        except HTTPStatusError as e:
            logger.error(f"Service {service.name} returned status code {e.response.status_code}. "
                         f"With Error: {e.response.text}")

        return False

