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

from dotenv import load_dotenv
from pathlib import Path 

BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / ".env")

# this is the Alembic Config object
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Get database URL dari config atau environment
# DATABASE_URL = config.get_main_option("sqlalchemy.url")
# if not DATABASE_URL:
#     # Fallback ke environment variable
DATABASE_URL = os.getenv("DATABASE_URL_MIGRATE")

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
