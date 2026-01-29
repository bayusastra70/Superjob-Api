"""add banner to companies

Revision ID: 0041
Revises: 0040
Create Date: 2026-01-29 10:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0041'
down_revision = '0040'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('companies', sa.Column('banner_url', sa.String(length=255), nullable=True))
    op.add_column('companies', sa.Column('banner_storage_id', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('companies', 'banner_storage_id')
    op.drop_column('companies', 'banner_url')
