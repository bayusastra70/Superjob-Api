from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

# from app.models.base import Base
from app.db.base import Base


class MasterWorkType(Base):
    """
    Model for master work types.
    Example: Full-time, Part-time, Contract, etc.
    """
    __tablename__ = "master_work_types"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=True)
    code = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, nullable=True)