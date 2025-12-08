from fastapi import FastAPI

from app.api import reminders
from app.api import job_quality
from app.models import reminder as reminder_model  # noqa: F401 - ensure models are loaded
from app.models import job_posting as job_posting_model  # noqa: F401 - ensure models are loaded

app = FastAPI(title="Superjob Corporate API")


app.include_router(reminders.router)
app.include_router(job_quality.router)
