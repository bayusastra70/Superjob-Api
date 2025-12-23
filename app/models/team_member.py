import enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
)
from sqlalchemy.sql import func, text
from sqlalchemy.orm import relationship


from app.db.base import Base


class TeamMemberRole(str, enum.Enum):
    ADMIN = "admin"
    HR_MANAGER = "hr_manager"
    RECRUITER = "recruiter"
    HIRING_MANAGER = "hiring_manager"
    TRAINER = "trainer"


class TeamMember(Base):
    """Model untuk team members/anggota tim perusahaan."""

    __tablename__ = "team_members"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    employer_id = Column(Integer, nullable=False, index=True)  # ID perusahaan/employer
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    # name dan email diambil dari relasi User, tidak disimpan di tabel ini
    role = Column(
        Enum(TeamMemberRole, name="team_member_role"),
        nullable=False,
        server_default=TeamMemberRole.RECRUITER.value,
    )
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    # Relasi ke User untuk mendapatkan name & email
    user = relationship("User", backref="team_memberships")
