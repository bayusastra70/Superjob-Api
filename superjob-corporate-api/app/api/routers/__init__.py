# Ekspor router secara eksplisit
from .auth import router as auth_router
from .health import router as health_router
from .candidate import router as candidate_router
from .chat import router as chat_router

from .chat_ws import router as chat_ws_router

from .job import router as job_router
from .application import router as application_router
from .candidate_application import router as candidate_application_router
from .rejection_reason import router as rejection_reason_router
from .company import router as company_router
from .activities import router as activities_router, actions_router as activities_actions_router
from .activity_ws import router as activity_ws_router
from .notification import router as notification_router

__all__ = [
    "auth_router", 
    "health_router", 
    "candidate_router", 
    "chat_router",
    "job_router",
    "application_router",
    "chat_ws_router",
    "candidate_application_router",
    "rejection_reason_router",
    "company_router",
    "activities_router",
    "activities_actions_router",
    "activity_ws_router",
    "notification_router"
]
