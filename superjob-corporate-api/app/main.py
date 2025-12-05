from fastapi import FastAPI

from app.api import reminders
from app.db.base import Base
from app.db.session import engine
from app.models import reminder as reminder_model  # noqa: F401 - ensure models are loaded

app = FastAPI(title="Superjob Corporate API")


@app.on_event("startup")
async def startup() -> None:
    # Ensure tables exist in dev; prefer running migrations in real environments.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.include_router(reminders.router)
