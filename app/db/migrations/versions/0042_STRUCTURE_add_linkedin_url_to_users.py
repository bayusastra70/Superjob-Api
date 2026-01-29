"""Add linkedin_url to users table

Revision ID: 0042
Revises:
Create Date: 2026-01-29
"""
from alembic import op
import sqlalchemy as sa

revision = '0042'
down_revision = '0041'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('users', sa.Column('linkedin_url', sa.String(255), nullable=True))

def downgrade():
    op.drop_column('users', 'linkedin_url')
