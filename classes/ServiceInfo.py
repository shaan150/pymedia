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
        return {
            "name": self.name,
            "type": self.type,
            "url": self.url,
            "cpu_used": self.cpu_used,
            "cpu_free": self.cpu_free,
            "memory_used": self.memory_used,
            "memory_free": self.memory_free,
            "total_memory": self.total_memory,
            "last_update": time.strftime('%Y-%m-%d %H:%M:%S', self.last_update),

        }

    async def calc_score(self):
        # Convert memory used to a percentage of total memory for scoring
        memory_used_percent = (self.memory_used / self.memory_free) * 100
        weighted_score = (self.cpu_used * CPU_WEIGHTING) + (memory_used_percent * MEMORY_WEIGHTING)
        return weighted_score

    async def calc_available_score(self):
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
        try:
            parsed_url = self.url.split(":")[0]
            # If the hostname is a domain name, resolve to IP, else it's already an IP
            return parsed_url
        except Exception as e:
            logger.error(f"An error occurred while extracting IP from URL: {str(e)}")
            return None
