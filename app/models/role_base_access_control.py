from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

# Junction tables
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
    Column('granted_at', DateTime, server_default=func.now()),
    Column('granted_by', Integer, ForeignKey('users.id', ondelete='SET NULL'))
)

user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('assigned_at', DateTime, server_default=func.now()),
    Column('assigned_by', Integer, ForeignKey('users.id', ondelete='SET NULL')),
    Column('expires_at', DateTime, nullable=True),
    Column('is_active', Boolean, server_default='true')
)


class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255))
    is_system = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship(
        "User", 
        secondary=user_roles, 
        primaryjoin="Role.id == user_roles.c.role_id",
        secondaryjoin="User.id == user_roles.c.user_id",
        back_populates="roles"
    )
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")


class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    module = Column(String(50), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


# Update User model (app/models/user.py) - tambah relationships
# Dalam User model, tambahkan:
# roles = relationship("Role", secondary=user_roles, back_populates="users")
# default_role = relationship("Role", foreign_keys=[default_role_id])