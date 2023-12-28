import asyncio
import sys
import time


class ServiceInfo:
    CPU_WEIGHTING = 0.65
    MEMORY_WEIGHTING = 0.35

    def __init__(self, name, type, url, cpu_usage=0, memory_usage=0, memory_free=0, cpu_free=0, users=[]):
        self.name = name
        self.type = type
        self.url = url
        self.cpu_used = cpu_usage
        self.cpu_free = cpu_free
        self.memory_used = memory_usage
        self.memory_free = memory_free
        self.users = users
        self.num_of_users = len(users)
        self.last_update = time.localtime()

    def __str__(self):
        return f"ServiceInfo(name={self.name}, type={self.type}, url={self.url}, cpu_usage={self.cpu_used}, " \
               f"memory_usage={self.memory_used}, users={self.users})"

    async def calc_cpu_score_per_user(self):
        return self.cpu_used / self.num_of_users

    async def calc_memory_score_per_user(self):
        return self.memory_used / self.num_of_users

    async def calc_score(self):
        user_cpu_score = await self.calc_cpu_score_per_user()
        user_memory_score = await self.calc_memory_score_per_user()
        if self.cpu_free - user_cpu_score == 0 or self.memory_free - user_memory_score:
            return 1

        global CPU_WEIGHTING, MEMORY_WEIGHTING
        weighted_score = (self.cpu_used * CPU_WEIGHTING) + (self.memory_used * MEMORY_WEIGHTING)

        return weighted_score

    async def checkIfUserExists(self, username, token):
        for user in self.users:
            if user.username == username and user.token == token:
                return True
        return False


async def select_service(services):
    scores = await asyncio.gather(*(s.calc_score() for s in services))
    return services[scores.index(min(scores))]
