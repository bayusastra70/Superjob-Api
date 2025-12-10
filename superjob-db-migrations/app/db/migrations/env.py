# # superjob-db-migrations/app/db/migrations/env.py

# from logging.config import fileConfig
# import os
# import sys

# from sqlalchemy import create_engine
# from sqlalchemy import pool

# from alembic import context

# # Tambahkan path ke sys.path agar bisa import dari root
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# # Import your Base and models
# from app.db.base import Base
# # Import all models so Alembic can discover them
# # Note: Karena ini repository migrasi terpusat, kita akan import model dari semua services
# # Untuk sekarang, kita impor dari talent-api dulu
# try:
#     from superjob_talent_api.app.models import Company, CompanyReview, User  # noqa: F401
#     print("Successfully imported models from talent-api", file=sys.stderr)
# except ImportError:
#     print("Warning: Could not import models from talent-api. Continuing...", file=sys.stderr)

# from dotenv import load_dotenv

# load_dotenv()

# # this is the Alembic Config object
# config = context.config

# # Setup logging
# if config.config_file_name is not None:
#     fileConfig(config.config_file_name)

# target_metadata = Base.metadata

# # ==== PERUBAHAN PENTING DI SINI ====
# # Hardcode URL yang kita tahu berhasil dari test
# DATABASE_URL = os.getenv("DATABASE_URL")
# # ===================================

# print(f"Using hardcoded database URL", file=sys.stderr)
# print(f"Current dir: {os.getcwd()}", file=sys.stderr)

# def run_migrations_offline() -> None:
#     """Run migrations in 'offline' mode."""
#     context.configure(
#         url=DATABASE_URL,
#         target_metadata=target_metadata,
#         literal_binds=True,
#         dialect_opts={"paramstyle": "named"},
#     )
    
#     with context.begin_transaction():
#         context.run_migrations()

# def run_migrations_online() -> None:
#     """Run migrations in 'online' mode."""
    
#     print(f"Creating engine with hardcoded URL...", file=sys.stderr)
    
#     # Create engine directly
#     connectable = create_engine(
#         DATABASE_URL,
#         poolclass=pool.NullPool
#     )
    
#     with connectable.connect() as connection:
#         print(f"Connected to database", file=sys.stderr)
        
#         context.configure(
#             connection=connection, 
#             target_metadata=target_metadata
#         )
        
#         with context.begin_transaction():
#             context.run_migrations()
#             print("Migrations completed successfully!", file=sys.stderr)

# if context.is_offline_mode():
#     run_migrations_offline()
# else:
#     run_migrations_online()

# superjob-db-migrations/app/db/migrations/env.py

# superjob-db-migrations/app/db/migrations/env.py
from logging.config import fileConfig
import os
import sys

from sqlalchemy import create_engine
from sqlalchemy import pool

from alembic import context

from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Tambahkan path ke sys.path agar bisa import dari root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Tambahkan path ke corporate-api
corporate_api_path = os.path.join(
    os.path.dirname(__file__), 
    '..', '..', '..', 
    'superjob-corporate-api'
)
if os.path.exists(corporate_api_path):
    sys.path.append(corporate_api_path)

# Import your Base and models
from app.db.base import Base

# Import all models so Alembic can discover them
try:
    from superjob_talent_api.app.models import Company, CompanyReview, User  # noqa: F401
    print("Successfully imported models from talent-api", file=sys.stderr)
except ImportError:
    print("Warning: Could not import models from talent-api. Continuing...", file=sys.stderr)

# IMPORT CORPORATE API MODELS
try:
    from superjob_corporate_api.app.models import *
    print("Successfully imported models from corporate-api", file=sys.stderr)
except ImportError:
    print("Warning: Could not import models from corporate-api. Continuing...", file=sys.stderr)

# this is the Alembic Config object
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

print(f"Using database URL from .env", file=sys.stderr)
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
    
    print(f"Creating engine with database URL...", file=sys.stderr)
    
    # Gunakan variable lokal untuk modifikasi URL
    db_url = DATABASE_URL
    
    # Pastikan DATABASE_URL pakai psycopg2 bukan asyncpg
    if db_url and "asyncpg" in db_url:
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        print(f"Converted asyncpg to psycopg2 in URL", file=sys.stderr)
    
    # Create engine directly
    connectable = create_engine(
        db_url,
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