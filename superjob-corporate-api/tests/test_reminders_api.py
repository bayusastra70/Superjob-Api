import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.db.base import Base
from app.main import app
from app.models.reminder import ReminderStatus


@pytest.fixture
def anyio_backend() -> str:
    # httpx.AsyncClient uses anyio under the hood; tell pytest to use asyncio.
    return "asyncio"


@pytest.fixture
async def db_sessionmaker(tmp_path):
    db_path = tmp_path / "test_reminders.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield SessionLocal
    await engine.dispose()


@pytest.fixture(autouse=True)
def override_dependencies(db_sessionmaker, monkeypatch):
    # Override DB dependency to use test DB
    async def _get_test_db():
        async with db_sessionmaker() as session:
            yield session

    app.dependency_overrides[get_db] = _get_test_db

    # Stub socket emissions to avoid network calls during tests.
    async def _noop(*args, **kwargs):
        return None

    monkeypatch.setattr("app.services.socketio_emitter.emit_reminder_created", _noop)
    monkeypatch.setattr("app.services.socketio_emitter.emit_reminder_updated", _noop)
    monkeypatch.setattr("app.services.socketio_emitter.emit_reminder_due", _noop)
    # Also patch the imported aliases inside the router module.
    monkeypatch.setattr("app.api.reminders.emit_reminder_created", _noop)
    monkeypatch.setattr("app.api.reminders.emit_reminder_updated", _noop)

    yield
    app.dependency_overrides.clear()


def _make_reminder_payload():
    return {
        "task_title": "Review candidates for Designer",
        "task_type": "candidate",
        "redirect_url": "/jobs/123/candidates",
        "job_id": str(uuid.uuid4()),
        "candidate_id": None,
        "due_at": None,
    }


@pytest.mark.anyio
async def test_create_reminder():
    employer_id = uuid.uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/employers/{employer_id}/reminders",
            json=_make_reminder_payload(),
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["employer_id"] == str(employer_id)
    assert data["status"] == ReminderStatus.pending.value
    assert data["task_title"] == "Review candidates for Designer"


@pytest.mark.anyio
async def test_update_reminder_forbidden_other_employer():
    owner_id = uuid.uuid4()
    other_id = uuid.uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create = await client.post(
            f"/employers/{owner_id}/reminders", json=_make_reminder_payload()
        )
        reminder_id = create.json()["id"]

        resp = await client.patch(
            f"/employers/{other_id}/reminders/{reminder_id}",
            json={"status": ReminderStatus.done.value},
        )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_list_reminders_pending_filter():
    employer_id = uuid.uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # create pending
        await client.post(
            f"/employers/{employer_id}/reminders", json=_make_reminder_payload()
        )
        # create then mark done
        create_done = await client.post(
            f"/employers/{employer_id}/reminders", json=_make_reminder_payload()
        )
        reminder_done_id = create_done.json()["id"]
        await client.patch(
            f"/employers/{employer_id}/reminders/{reminder_done_id}",
            json={"status": ReminderStatus.done.value},
        )

        resp_pending = await client.get(
            f"/employers/{employer_id}/reminders", params={"status": "pending"}
        )
        resp_all = await client.get(f"/employers/{employer_id}/reminders", params={"status": ""})

    assert resp_pending.status_code == 200
    pending_items = resp_pending.json()
    assert len(pending_items) == 1
    assert pending_items[0]["status"] == "pending"

    assert resp_all.status_code == 200
    assert len(resp_all.json()) == 2
