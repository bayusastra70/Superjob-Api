"""add auth_provider to users

Revision ID: 0024
Revises: 0023
Create Date: 2026-01-14 18:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0024'
down_revision = '0023'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('auth_provider', sa.String(length=50), server_default='email', nullable=False))


def downgrade():
    op.drop_column('users', 'auth_provider')
