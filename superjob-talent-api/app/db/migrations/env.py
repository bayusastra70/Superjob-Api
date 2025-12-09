from logging.config import fileConfig
import os
import sys

from sqlalchemy import create_engine
from sqlalchemy import pool

from alembic import context

# Import your Base and models
from app.db.base import Base
# Import all models so Alembic can discover them
from app.models import Company, CompanyReview, User  # noqa: F401
from dotenv import load_dotenv

load_dotenv()

# this is the Alembic Config object
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# ==== PERUBAHAN PENTING DI SINI ====
# Hardcode URL yang kita tahu berhasil dari test
DATABASE_URL = os.getenv("DATABASE_URL")
# ===================================

print(f"Using hardcoded database URL", file=sys.stderr)
print(f"Current dir: {os.getcwd()}", file=sys.stderr)

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
    
    print(f"Creating engine with hardcoded URL...", file=sys.stderr)
    
    # Create engine directly
    connectable = create_engine(
        DATABASE_URL,
        poolclass=pool.NullPool
    )
    
    with connectable.connect() as connection:
        print(f"Connected to database", file=sys.stderr)
        
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )
        
        with context.begin_transaction():
            context.run_migrations()
            print("Migrations completed successfully!", file=sys.stderr)

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
