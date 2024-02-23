import DatabaseAsyncQuery
from classes.enum.ServiceType import ServiceType
from classes.services.ExtendedService import ExtendedService


class DatabaseService(ExtendedService):
    def __init__(self):
        super().__init__(ServiceType.DATABASE_SERVICE)

    async def start_background_tasks(self):
        await super().start_background_tasks()
        await DatabaseAsyncQuery.create_tables()