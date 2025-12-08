import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models import job_posting  # noqa: F401 - ensure model registration
from app.models import reminder  # noqa: F401 - ensure model registration
from app.api.deps import get_db
from app.main import app


@pytest.fixture
def anyio_backend() -> str:
    # httpx/anyio need an explicit backend.
    return "asyncio"


@pytest.fixture
async def db_engine(tmp_path):
    db_path = tmp_path / "test_reminders.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
def db_sessionmaker(db_engine):
    return async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(autouse=True)
def override_dependencies(db_sessionmaker, monkeypatch):
    async def _get_test_db():
        async with db_sessionmaker() as session:
            yield session

    app.dependency_overrides[get_db] = _get_test_db

    async def _noop(*args, **kwargs):
        return None

    monkeypatch.setattr("app.services.socketio_emitter.emit_reminder_created", _noop, raising=False)
    monkeypatch.setattr("app.services.socketio_emitter.emit_reminder_updated", _noop, raising=False)
    monkeypatch.setattr("app.services.socketio_emitter.emit_reminder_due", _noop, raising=False)
    monkeypatch.setattr("app.api.reminders.emit_reminder_created", _noop, raising=False)
    monkeypatch.setattr("app.api.reminders.emit_reminder_updated", _noop, raising=False)

    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def clear_quality_cache():
    from app.api import job_quality

    job_quality.clear_job_score_cache()
    yield
    job_quality.clear_job_score_cache()
