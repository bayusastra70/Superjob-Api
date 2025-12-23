from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging


# from app.services.database import init_database
from app.core.config import settings
from app.api.routers import auth, health, candidate

from app.api import (
    auth_router,
    health_router,
    candidate_router,
    chat_router,
    job_router,
    application_router,
    chat_ws_router,
    interview_router,
)
from app.api.ws import interview_ws_router
from app.api.routers import (
    candidate_application_router,
    rejection_reason_router,
    company_router,
    activities_router,
    activities_actions_router,
    activity_ws_router,
    notification_router,
    companies_router,
    interview_feedback_router,
    team_member_router,
    user_router
)

from app.api import reminders
from app.api import job_quality
from app.api import dashboard
from app.api import employer_resources

from app.models import reminder as reminder_model
from app.models import job as job_model
from app.models import candidate_application as candidate_application_model
from app.models import rejection_reason as rejection_reason_model
from app.models import audit_log as audit_log_model
from app.core.monitoring import init_sentry, register_timing_middleware

from fastapi.exceptions import RequestValidationError, HTTPException

from app.exceptions import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
# init_database()
init_sentry()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_timing_middleware(app)

# Authentication routers
app.include_router(auth_router)
app.include_router(health_router)
app.include_router(candidate_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)

app.include_router(chat_ws_router)
app.include_router(activity_ws_router)
app.include_router(interview_ws_router)
app.include_router(notification_router, prefix=settings.API_V1_STR)
app.include_router(companies_router, prefix=settings.API_V1_STR)

app.include_router(job_router, prefix=settings.API_V1_STR)
app.include_router(application_router, prefix=settings.API_V1_STR)
app.include_router(candidate_application_router, prefix=settings.API_V1_STR)
app.include_router(rejection_reason_router, prefix=settings.API_V1_STR)
app.include_router(company_router, prefix=settings.API_V1_STR)
app.include_router(activities_router, prefix=settings.API_V1_STR)
app.include_router(activities_actions_router, prefix=settings.API_V1_STR)
app.include_router(activity_ws_router)
app.include_router(interview_router, prefix=settings.API_V1_STR)

app.include_router(reminders.router, prefix=settings.API_V1_STR)
app.include_router(job_quality.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)
app.include_router(employer_resources.router, prefix=settings.API_V1_STR)

app.include_router(interview_feedback_router, prefix=settings.API_V1_STR)
app.include_router(team_member_router, prefix=settings.API_V1_STR)
app.include_router(user_router, prefix=settings.API_V1_STR)


app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore
app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore
app.add_exception_handler(Exception, general_exception_handler)  # type: ignore


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
