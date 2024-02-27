import asyncio
import socket
import sys
import time
from datetime import datetime
from urllib.parse import urlparse

from fastapi.logger import logger

from classes.enum.ServiceType import ServiceType

CPU_WEIGHTING = 0.65
MEMORY_WEIGHTING = 0.35


class ServiceInfo:
    """
    :class: ServiceInfo

    This class represents information about a service.

    :ivar name: The name of the service.
    :type name: str
    :ivar type: The type of the service.
    :type type: str
    :ivar url: The URL of the service.
    :type url: str
    :ivar cpu_used: The CPU usage of the service.
    :type cpu_used: float
    :ivar cpu_free: The CPU free of the service.
    :type cpu_free: float
    :ivar memory_used: The memory usage of the service.
    :type memory_used: float
    :ivar memory_free: The memory free of the service.
    :type memory_free: float
    :ivar total_memory: The total memory of the service.
    :type total_memory: float
    :ivar last_update: The last update time of the service.
    :type last_update: datetime.datetime
    :ivar creation_time: The creation time of the service.
    :type creation_time: datetime.datetime

    Methods
    -------

    __init__(self, name, service_type, url, cpu_usage=0, memory_usage=0, memory_free=0, total_memory=0, cpu_free=0):
        Initializes a new instance of the ServiceInfo class.

        :param name: The name of the service.
        :type name: str
        :param service_type: The type of the service.
        :type service_type: str
        :param url: The URL of the service.
        :type url: str
        :param cpu_usage: The CPU usage of the service.
        :type cpu_usage: float, optional
        :param memory_usage: The memory usage of the service.
        :type memory_usage: float, optional
        :param memory_free: The memory free of the service.
        :type memory_free: float, optional
        :param total_memory: The total memory of the service.
        :type total_memory: float, optional
        :param cpu_free: The CPU free of the service.
        :type cpu_free: float, optional

    __str__(self):
        Returns a string representation of the ServiceInfo object.

        :return: The string representation of the ServiceInfo object.
        :rtype: str

    to_dict(self):
        Converts the ServiceInfo object to a dictionary.

        :return: The dictionary representation of the ServiceInfo object.
        :rtype: dict

    calc_score(self):
        Calculates the score of the ServiceInfo object.

        :return: The calculated score.
        :rtype: float

    calc_available_score(self):
        Calculates the available score of the ServiceInfo object.

        :return: The calculated available score.
        :rtype: float

    extract_ip_from_url(self):
        Extracts the IP address from the URL.

        :return: The extracted IP address or None if extraction fails.
        :rtype: str or None
    """
    def __init__(self, name, service_type, url, cpu_usage=0, memory_usage=0, memory_free=0, total_memory=0, cpu_free=0):

        self.name = name
        self.type = service_type
        self.url = url
        self.cpu_used = cpu_usage
        self.cpu_free = cpu_free
        self.memory_used = memory_usage
        self.memory_free = memory_free
        self.total_memory = total_memory
        self.last_update = datetime.now()
        self.creation_time = None
        print(f"CPU Free: {self.cpu_free}, Type: {type(self.cpu_free)}")

    def __str__(self):
        return f"ServiceInfo(name={self.name}, type={self.type}, url={self.url}, cpu_usage={self.cpu_used}, " \
               f"memory_usage={self.memory_used}"

    def to_dict(self):
        """
        Returns a dictionary representation of the object.

        :return: A dictionary containing the object's properties:
                 - "name"
                 - "type"
                 - "url"
                 - "cpu_used"
                 - "cpu_free"
                 - "memory_used"
                 - "memory_free"
                 - "total_memory"
                 - "last_update"
                 The "last_update" property is formatted as a string in the format '%Y-%m-%d %H:%M:%S'.
        """
        return {
            "name": self.name,
            "type": self.type,
            "url": self.url,
            "cpu_used": self.cpu_used,
            "cpu_free": self.cpu_free,
            "memory_used": self.memory_used,
            "memory_free": self.memory_free,
            "total_memory": self.total_memory,
            "last_update": self.last_update.strftime('%Y-%m-%d %H:%M:%S')
        }

    async def calc_score(self):
        """
        Calculate the weighted score based on CPU and memory usage.

        :return: The calculated weighted score.
        :rtype: float
        """
        if (self.memory_free <= 0 or self.total_memory <= 0 or self.memory_free - self.memory_used <= 0
                or self.cpu_free <= 0 or self.cpu_free - self.cpu_used <= 0):
            return 1
        # Convert memory used to a percentage of total memory for scoring
        memory_used_percent = (self.memory_used / self.memory_free) * 100
        weighted_score = (self.cpu_used * CPU_WEIGHTING) + (memory_used_percent * MEMORY_WEIGHTING)
        return weighted_score / 100

    async def calc_available_score(self):
        """
        Calculate the available score based on CPU and memory information.

        :return: The available score as a float value.
        """
        # Ensure total_memory is more than 0 to avoid division by zero
        if self.total_memory <= 0:
            return 0

        # Convert memory free to a percentage of total memory for scoring
        memory_free_percent = (self.memory_free / self.total_memory) * 100

        # Calculate the available score as a weighted sum of the CPU and memory scores
        available_score = ((float(self.cpu_free) * CPU_WEIGHTING) + (
                    float(memory_free_percent) * MEMORY_WEIGHTING)) / 100

        return available_score

    async def extract_ip_from_url(self):
        """
        Extracts the IP address from the given URL.

        :return: The IP address extracted from the URL.
        """
        try:
            parsed_url = self.url.split(":")[0]
            # If the hostname is a domain name, resolve to IP, else it's already an IP
            return parsed_url
        except Exception as e:
            logger.error(f"An error occurred while extracting IP from URL: {str(e)}")
            return None
