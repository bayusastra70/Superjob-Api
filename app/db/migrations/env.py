from logging.config import fileConfig
import os
import sys

from sqlalchemy import create_engine
from sqlalchemy import pool, text

from alembic import context

# Import Base
from app.db.base import Base
from app.models import *  # noqa: F401

from dotenv import load_dotenv
from pathlib import Path 

BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / ".env")

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
DATABASE_URL = os.getenv("DATABASE_URL_MIGRATE")

def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)
    
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        
        with context.begin_transaction():
            context.run_migrations()
            
            print("🔄 Fixing sequences...")
            try:
                # PASTI WORK - tanpa format() yang ribet
                connection.execute(text("""
                    DO $$
                    DECLARE 
                        r RECORD;
                        seq_name TEXT;
                    BEGIN
                        FOR r IN
                            SELECT 
                                table_name,
                                column_name,
                                column_default
                            FROM information_schema.columns
                            WHERE column_default LIKE 'nextval%%'
                                AND table_schema = 'public'
                        LOOP
                            BEGIN
                                -- Extract sequence name from DEFAULT clause
                                seq_name := split_part(split_part(r.column_default, '''', 2), '''', 1);
                                
                                -- Set sequence value
                                EXECUTE 'SELECT setval(''' || seq_name || ''', ' ||
                                        'COALESCE((SELECT MAX(' || quote_ident(r.column_name) || ') FROM ' || 
                                        quote_ident(r.table_name) || '), 1), true)';
                            EXCEPTION WHEN OTHERS THEN
                                -- Skip jika error
                                NULL;
                            END;
                        END LOOP;
                    END $$;
                """))
                print("✅ Sequences fixed!")
            except Exception as e:
                print(f"⚠️  Sequence fix skipped: {e}")

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()