"""Add nib_document_storage_id to companies table

Revision ID: 0025
Revises: 0024
Create Date: 2026-01-15 14:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0025'
down_revision = '0024'
branch_labels = None
depends_on = None


def upgrade():
    # Add nib_document_storage_id and logo_storage_id columns to store Solvera Storage file IDs
    op.add_column('companies', sa.Column('nib_document_storage_id', sa.String(length=255), nullable=True))
    op.add_column('companies', sa.Column('logo_storage_id', sa.String(length=255), nullable=True))


def downgrade():
    # Remove storage ID columns
    op.drop_column('companies', 'logo_storage_id')
    op.drop_column('companies', 'nib_document_storage_id')
