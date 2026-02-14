# Import models to ensure they are registered with SQLAlchemy
from app.models import reminder  # noqa: F401
from app.models import job  # noqa: F401
from app.models import job_performance_daily  # noqa: F401
from app.models import candidate_application  # noqa: F401
from app.models import rejection_reason  # noqa: F401
from app.models import audit_log  # noqa: F401
from app.models import activity_log  # noqa: F401
from app.models import user  # noqa: F401
from app.models import company  # noqa: F401
from app.models import company_review  # noqa: F401
from app.models import interview  # noqa: F401
from app.models import user_company  # noqa: F401
from app.models import candidate_info  # noqa: F401
from app.models import ojt_program  # noqa: F401
from app.models import ojt_application  # noqa: F401

from app.models.role_base_access_control import Role, Permission


__all__ = [
    "reminder",
    "job",
    "job_performance_daily",
    "candidate_application",
    "rejection_reason",
    "audit_log",
    "activity_log",
    "user",
    "company",
    "company_review",
    "interview",
    "user_company",
    
    "Role",      # TAMBAHKAN
    "Permission", # TAMBAHKAN

    "candidate_info",
    "ojt_program",
    "ojt_application",
]
