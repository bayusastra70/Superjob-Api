from fastapi import FastAPI

from app.api import reminders
from app.api import job_quality
from app.api import dashboard
from app.api import employer_resources
from app.models import reminder as reminder_model  # noqa: F401 - ensure models are loaded
from app.models import job_posting as job_posting_model  # noqa: F401 - ensure models are loaded
from app.core.monitoring import init_sentry, register_timing_middleware

app = FastAPI(title="Superjob Corporate API")

# Monitoring setup
init_sentry()
register_timing_middleware(app)

app.include_router(reminders.router)
app.include_router(job_quality.router)
app.include_router(dashboard.router)
app.include_router(employer_resources.router)
