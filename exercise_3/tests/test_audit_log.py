import pytest
import pytest_asyncio
import uuid
import aiosqlite
from datetime import datetime, timezone

from exercise_3.infrastructure.database.audit_repository import SQLiteAuditLogRepository
from exercise_3.domain.models import AuditLogEntry


@pytest.fixture
def memory_db_uri(tmp_path):
    db_file = tmp_path / "test_audit.db"
    return str(db_file)


@pytest_asyncio.fixture
async def repository(memory_db_uri):
    repo = SQLiteAuditLogRepository(db_path=memory_db_uri)
    await repo.initialize_schema()
    yield repo


@pytest.mark.asyncio
async def test_insert_audit_log_entry_is_persisted(repository, memory_db_uri):
    entry = AuditLogEntry(
        id=uuid.uuid4(),
        alert_id="alert-1234",
        from_status="new",
        to_status="investigating",
        changed_by="admin_user",
        changed_at=datetime.now(timezone.utc),
        reason="Manual investigation started",
    )

    await repository.insert(entry)

    async with aiosqlite.connect(memory_db_uri) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            "SELECT * FROM audit_log WHERE id = ?", (str(entry.id),)
        ) as cursor:
            row = await cursor.fetchone()

    assert row is not None
    assert row["id"] == str(entry.id)
    assert row["alert_id"] == "alert-1234"
    assert row["from_status"] == "new"
    assert row["to_status"] == "investigating"
    assert row["changed_by"] == "admin_user"
    assert row["changed_at"] == entry.changed_at.isoformat()
    assert row["reason"] == "Manual investigation started"
