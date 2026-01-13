"""add nib_document_url to companies

Revision ID: 0022
Revises: 0021
Create Date: 2026-01-12 19:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0022'
down_revision = '0021'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('companies', sa.Column('nib_document_url', sa.Text(), nullable=True))
    op.add_column('companies', sa.Column('is_verified', sa.Boolean(), server_default='false', nullable=False))


def downgrade():
    op.drop_column('companies', 'is_verified')
    op.drop_column('companies', 'nib_document_url')
