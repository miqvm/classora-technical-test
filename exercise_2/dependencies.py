from motor.motor_asyncio import AsyncIOMotorClient

from exercise_2.application.services import AlertService
from exercise_2.config import settings
from exercise_2.infrastructure.database.repository import (
    MongoAlertRepository,
)

# Initialize MongoDB async client connection
client = AsyncIOMotorClient(settings.mongo_uri)

# Get the database instance
database = client[settings.mongo_database]

# Create repository instance for alerts collection
repository = MongoAlertRepository(database.alerts)

# Create service instance with repository dependency injection
service = AlertService(repository)


def get_alert_service() -> AlertService:
    # Return the singleton service instance for dependency injection
    return service
