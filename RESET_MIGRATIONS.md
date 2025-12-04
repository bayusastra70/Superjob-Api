# How to Reset All Migrations and Start Fresh

This guide will help you completely reset your database migrations and start from scratch.

## ⚠️ WARNING

**This will delete all data in your database!** Only do this in development environments.

## Steps to Reset Migrations

### Option 1: Complete Reset (Recommended for Development)

1. **Drop all tables from the database**

   ```bash
   # Connect to your database and drop all tables
   # Or use this Python script (see below)
   ```

2. **Delete the Alembic version table**

   ```bash
   # This table tracks which migrations have been applied
   # It will be automatically recreated when you run the first migration
   ```

3. **Delete all migration files**

   ```bash
   # Delete all files in app/db/migrations/versions/ except __pycache__
   ```

4. **Create a new initial migration**

   ```bash
   alembic revision --autogenerate -m "initial migration"
   ```

5. **Apply the migration**
   ```bash
   alembic upgrade head
   ```

### Option 2: Using SQL Commands

If you have direct database access, you can run:

```sql
-- Drop all tables (PostgreSQL)
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;
```

Then follow steps 3-5 from Option 1.

### Option 3: Using Python Script

Run this Python script to automate the process:

```python
# reset_migrations.py
from sqlalchemy import create_engine, text
from app.core.config import settings

# Create engine
engine = create_engine(settings.DATABASE_URL)

# Drop all tables
with engine.connect() as conn:
    conn.execute(text("DROP SCHEMA public CASCADE"))
    conn.execute(text("CREATE SCHEMA public"))
    conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
    conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
    conn.commit()

print("All tables dropped successfully!")
```

Then follow steps 3-5 from Option 1.

## Quick Command Reference

```bash
# 1. Delete all migration files (Windows PowerShell)
Remove-Item app\db\migrations\versions\*.py -Exclude __init__.py

# 2. Create new initial migration
alembic revision --autogenerate -m "initial migration"

# 3. Apply migration
alembic upgrade head
```

## After Reset

1. Review the generated migration file to ensure it matches your current models
2. Test that your application works correctly
3. Commit the new migration file to version control

## Notes

- The `alembic_version` table will be automatically created when you run your first migration
- Make sure all your models are properly imported in `app/db/migrations/env.py`
- If you have data you want to keep, export it before resetting
