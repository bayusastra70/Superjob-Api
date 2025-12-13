# Import models to ensure they are registered with SQLAlchemy
from app.models import reminder  # noqa: F401
from app.models import job_posting  # noqa: F401
from app.models import job_performance_daily  # noqa: F401
from app.models import candidate_application  # noqa: F401
from app.models import rejection_reason  # noqa: F401
from app.models import audit_log  # noqa: F401
from app.models import activity_log  # noqa: F401


__all__ = [
    "reminder",
    "job_posting",
    "job_performance_daily",
    "candidate_application",
    "rejection_reason",
    "audit_log",
    "activity_log",
]