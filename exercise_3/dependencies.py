from motor.motor_asyncio import AsyncIOMotorClient

from exercise_3.application.services import AlertService
from exercise_3.config import settings
from exercise_3.infrastructure.database.audit_repository import SQLiteAuditLogRepository
from exercise_3.infrastructure.database.repository import (
    MongoAlertRepository,
)
from exercise_3.infrastructure.external.threat_client import (
    HttpxThreatEnrichmentService,
)

# Initialize MongoDB async client connection
client = AsyncIOMotorClient(settings.mongo_uri)

# Get the database instance
database = client[settings.mongo_database]

# Create repository instances
repository = MongoAlertRepository(database.alerts)

# Use settings for the SQLite database path
audit_repository = SQLiteAuditLogRepository(db_path=settings.sqlite_audit_db_path)

# Use settings for the External API Base URL
enrichment_service = HttpxThreatEnrichmentService(
    base_url=settings.threat_intel_base_url
)

# Create service instance with repository, audit, and enrichment dependency injection
service = AlertService(
    repository=repository,
    audit_repository=audit_repository,
    enrichment_service=enrichment_service,
)


def get_alert_service() -> AlertService:
    return service
