# import asyncio
# from logging.config import fileConfig

# from alembic import context
# from sqlalchemy import pool
# from sqlalchemy.engine import Connection
# from sqlalchemy.ext.asyncio import async_engine_from_config

# from app.core.config import settings
# from app.db.base import Base
# from app.models import reminder  # noqa: F401 - ensure models are imported
# from app.models import job_posting  # noqa: F401 - ensure models are imported
# from app.models import job_performance_daily  # noqa: F401 - ensure models are imported
# from app.models import candidate_application  # noqa: F401 - ensure models are imported
# from app.models import rejection_reason  # noqa: F401 - ensure models are imported
# from app.models import audit_log  # noqa: F401 - ensure models are imported

# # Alembic Config object, provides access to values in alembic.ini.
# config = context.config

# if config.config_file_name is not None:
#     fileConfig(config.config_file_name)

# # Prefer runtime DB URL (from .env via settings)
# config.set_main_option("sqlalchemy.url", settings.database_url)

# # Metadata for autogenerate
# target_metadata = Base.metadata


# def run_migrations_offline() -> None:
#     """Run migrations in 'offline' mode."""
#     url = config.get_main_option("sqlalchemy.url")
#     context.configure(
#         url=url,
#         target_metadata=target_metadata,
#         literal_binds=True,
#         dialect_opts={"paramstyle": "named"},
#     )

#     with context.begin_transaction():
#         context.run_migrations()


# def do_run_migrations(connection: Connection) -> None:
#     context.configure(connection=connection, target_metadata=target_metadata)
#     with context.begin_transaction():
#         context.run_migrations()


# async def run_migrations_online() -> None:
#     """Run migrations in 'online' mode with async engine."""
#     connectable = async_engine_from_config(
#         config.get_section(config.config_ini_section),
#         prefix="sqlalchemy.",
#         poolclass=pool.NullPool,
#     )

#     async with connectable.connect() as connection:
#         await connection.run_sync(do_run_migrations)

#     await connectable.dispose()


# if context.is_offline_mode():
#     run_migrations_offline()
# else:
#     asyncio.run(run_migrations_online())

# superjob-corporate-api/migrations/env.py
# GANTI FILE INI MENJADI:

from logging.config import fileConfig
import os
import sys

from sqlalchemy import create_engine
from sqlalchemy import pool

from alembic import context

# Import Base dari corporate-api
from app.db.base import Base
# Import models
from app.models import *  # noqa: F401

# this is the Alembic Config object
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Get database URL dari config atau environment
DATABASE_URL = config.get_main_option("sqlalchemy.url")
if not DATABASE_URL:
    # Fallback ke environment variable
    DATABASE_URL = os.getenv("DATABASE_URL")

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_engine(
        DATABASE_URL,
        poolclass=pool.NullPool
    )
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )
        
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
