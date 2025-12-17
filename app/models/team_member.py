import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.sql import func, text

from app.db.base import Base


class TeamMemberRole(str, enum.Enum):
    ADMIN = "admin"
    HR_MANAGER = "hr_manager"
    RECRUITER = "recruiter"
    HIRING_MANAGER = "hiring_manager"
    VIEWER = "viewer"


class TeamMember(Base):
    """Model untuk team members/anggota tim perusahaan."""

    __tablename__ = "team_members"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    employer_id = Column(Integer, nullable=False, index=True)  # ID perusahaan/employer
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(
        Enum(TeamMemberRole, name="team_member_role", create_constraint=False),
        nullable=False,
        server_default=TeamMemberRole.VIEWER.value,
    )
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
