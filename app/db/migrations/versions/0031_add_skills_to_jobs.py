# File: alembic/versions/0030_add_skills_to_jobs.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0031'
down_revision = '0030'


def upgrade():
    op.add_column('jobs', 
        sa.Column('skills', postgresql.JSONB(), nullable=True)
    )


def downgrade():
    op.drop_column('jobs', 'skills')