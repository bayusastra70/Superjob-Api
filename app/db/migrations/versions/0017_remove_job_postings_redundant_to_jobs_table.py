"""Remove redundant job_postings table

Revision ID: 0017_remove_job_postings_table
Revises: 0016
Create Date: 2025-12-23

This migration removes the redundant job_postings table since its functionality
has been fully migrated to the jobs table with additional columns.

Important: This migration handles:
1. Foreign key constraints from other tables to job_postings
2. Data preservation if needed (though job_postings was for testing only)
3. Clean removal of the table and related dependencies
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0017'
down_revision = '0016'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========== STEP 1: Check and handle foreign key dependencies ==========
    
    # Check if reminder_tasks table has foreign key to job_postings
    # We need to drop this constraint first
    try:
        # Drop foreign key constraint from reminder_tasks to job_postings
        op.drop_constraint(
            'reminder_tasks_job_id_fkey',
            'reminder_tasks',
            type_='foreignkey'
        )
    except Exception as e:
        print(f"Note: Foreign key constraint 'reminder_tasks_job_id_fkey' may not exist: {e}")
    
    # ========== STEP 2: Update reminder_tasks data ==========
    
    # For any reminder_tasks that reference job_postings, we should either:
    # 1. Set job_id to NULL (if the job posting no longer exists)
    # 2. Or update to reference a valid job ID from jobs table if possible
    
    # Since job_postings was mainly for testing, we'll set job_id to NULL
    op.execute("""
        UPDATE reminder_tasks 
        SET job_id = NULL 
        WHERE job_id IS NOT NULL 
        AND job_id IN (SELECT id FROM job_postings)
    """)
    
    # Also change the job_id column type from String to Integer to match jobs table
    # But first, let's keep it as String for backward compatibility
    
    # ========== STEP 3: Drop the job_postings table ==========
    
    # First drop any indexes
    try:
        op.drop_index('ix_job_postings_employer_id', table_name='job_postings')
    except Exception as e:
        print(f"Note: Index 'ix_job_postings_employer_id' may not exist: {e}")
    
    try:
        op.drop_index('ix_job_postings_status', table_name='job_postings')
    except Exception as e:
        print(f"Note: Index 'ix_job_postings_status' may not exist: {e}")
    
    # Now drop the table
    op.drop_table('job_postings')
    
    # ========== STEP 4: Update reminder_tasks job_id column ==========
    
    # Change job_id column from String to Integer since it should now reference jobs.id
    # First, we need to clear any remaining string values
    op.execute("""
        UPDATE reminder_tasks 
        SET job_id = NULL 
        WHERE job_id IS NOT NULL 
        AND job_id ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    """)
    
    # Create a new integer column
    op.add_column(
        'reminder_tasks',
        sa.Column('job_id_int', sa.Integer(), nullable=True)
    )
    
    # Try to convert existing numeric string IDs to integers
    op.execute("""
        UPDATE reminder_tasks 
        SET job_id_int = CAST(job_id AS INTEGER) 
        WHERE job_id IS NOT NULL 
        AND job_id ~ '^[0-9]+$'
    """)
    
    # Drop the old string column
    op.drop_column('reminder_tasks', 'job_id')
    
    # Rename the new column to job_id
    op.alter_column('reminder_tasks', 'job_id_int', new_column_name='job_id')
    
    # Add foreign key constraint to jobs table
    op.create_foreign_key(
        'fk_reminder_tasks_job_id_jobs',
        'reminder_tasks',
        'jobs',
        ['job_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # Create index for better performance
    op.create_index(
        'ix_reminder_tasks_job_id',
        'reminder_tasks',
        ['job_id']
    )


def downgrade() -> None:
    # ========== STEP 1: Recreate job_postings table ==========
    
    # First recreate the enum type if needed
    op.execute("""
        DO $$ 
        BEGIN 
            CREATE TYPE job_status AS ENUM ('draft', 'published', 'archived');
        EXCEPTION 
            WHEN duplicate_object THEN 
                NULL;
        END $$;
    """)
    
    # Recreate the job_postings table with original structure
    op.create_table(
        'job_postings',
        sa.Column(
            'id',
            sa.String(length=36),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column('employer_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('salary_min', sa.Numeric(12, 2), nullable=True),
        sa.Column('salary_max', sa.Numeric(12, 2), nullable=True),
        sa.Column('salary_currency', sa.String(length=8), nullable=True),
        sa.Column('skills', sa.JSON(), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('employment_type', sa.String(length=50), nullable=True),
        sa.Column('experience_level', sa.String(length=50), nullable=True),
        sa.Column('education', sa.String(length=100), nullable=True),
        sa.Column('benefits', sa.Text(), nullable=True),
        sa.Column('contact_url', sa.String(length=512), nullable=True),
        sa.Column(
            'status',
            postgresql.ENUM(
                'draft', 'published', 'archived', name='job_status', create_type=False
            ),
            nullable=False,
            server_default='draft',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['employer_id'],
            ['users.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Recreate indexes
    op.create_index('ix_job_postings_status', 'job_postings', ['status'])
    op.create_index('ix_job_postings_employer_id', 'job_postings', ['employer_id'])
    
    # ========== STEP 2: Restore reminder_tasks foreign key to job_postings ==========
    
    # Drop current foreign key to jobs
    op.drop_constraint(
        'fk_reminder_tasks_job_id_jobs',
        'reminder_tasks',
        type_='foreignkey'
    )
    
    # Drop index on job_id
    op.drop_index('ix_reminder_tasks_job_id', table_name='reminder_tasks')
    
    # Change job_id column back to String
    op.add_column(
        'reminder_tasks',
        sa.Column('job_id_string', sa.String(length=36), nullable=True)
    )
    
    # Drop the integer column
    op.drop_column('reminder_tasks', 'job_id')
    
    # Rename the string column to job_id
    op.alter_column('reminder_tasks', 'job_id_string', new_column_name='job_id')
    
    # Recreate foreign key constraint to job_postings
    op.create_foreign_key(
        'reminder_tasks_job_id_fkey',
        'reminder_tasks',
        'job_postings',
        ['job_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # ========== STEP 3: Insert sample data into job_postings for backward compatibility ==========
    
    # Insert some sample data that was in the seed migration
    op.execute("""
        INSERT INTO job_postings (id, employer_id, title, description, status, created_at, updated_at) 
        VALUES 
        ('11111111-1111-1111-1111-111111111111', 8, 'Senior Software Engineer', 'Sample job posting', 'published', NOW(), NOW()),
        ('11111111-1111-1111-1111-111111111112', 8, 'Junior Frontend Developer', 'Sample job posting', 'published', NOW(), NOW()),
        ('11111111-1111-1111-1111-111111111113', 3, 'UI/UX Designer', 'Sample job posting', 'published', NOW(), NOW())
        ON CONFLICT (id) DO NOTHING;
    """)
    
    # ========== STEP 4: Update reminder_tasks with job_postings IDs ==========
    
    # Update some reminder_tasks to reference the recreated job_postings
    op.execute("""
        UPDATE reminder_tasks 
        SET job_id = '11111111-1111-1111-1111-111111111111'
        WHERE id = 'aaaa1111-aaaa-1111-aaaa-111111111111';
        
        UPDATE reminder_tasks 
        SET job_id = '11111111-1111-1111-1111-111111111112'
        WHERE id = 'aaaa1111-aaaa-1111-aaaa-111111111112';
        
        UPDATE reminder_tasks 
        SET job_id = '11111111-1111-1111-1111-111111111114'
        WHERE id = 'aaaa1111-aaaa-1111-aaaa-111111111114';
    """)