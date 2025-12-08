from fastapi import FastAPI

from app.api import reminders
from app.models import reminder as reminder_model  # noqa: F401 - ensure models are loaded

app = FastAPI(title="Superjob Corporate API")


app.include_router(reminders.router)
