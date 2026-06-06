import aiosqlite

from exercise_3.domain.models import AuditLogEntry
from exercise_3.domain.ports import AuditLogRepository


class SQLiteAuditLogRepository(AuditLogRepository):
    def __init__(self, db_path: str = "audit.db"):
        self._db_path = db_path

    async def initialize_schema(self) -> None:
        """
        Creates the immutable audit_log table if it doesn't already exist.
        This should be called during application startup.
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS audit_log (
            id TEXT PRIMARY KEY,
            alert_id TEXT NOT NULL,
            from_status TEXT NOT NULL,
            to_status TEXT NOT NULL,
            changed_by TEXT NOT NULL,
            changed_at TIMESTAMP NOT NULL,
            reason TEXT
        );
        """
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(create_table_sql)
            await db.commit()

    async def insert(self, entry: AuditLogEntry) -> None:
        """
        Appends a new audit log entry to the database.
        No UPDATE or DELETE methods are provided to enforce immutability.
        """
        insert_sql = """
        INSERT INTO audit_log (
            id, alert_id, from_status, to_status, 
            changed_by, changed_at, reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                insert_sql,
                (
                    str(entry.id),  # UUID converted to string for SQLite
                    entry.alert_id,
                    entry.from_status,
                    entry.to_status,
                    entry.changed_by,
                    entry.changed_at.isoformat(),  # Store datetime as ISO 8601 string
                    entry.reason,
                ),
            )
            await db.commit()
