"""add ojt application details

Revision ID: 0060
Revises: 0059
Create Date: 2026-02-19 09:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0060'
down_revision = '0059'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to ojt_applications
    op.add_column('ojt_applications', sa.Column('full_name', sa.String(length=255), nullable=True))
    op.add_column('ojt_applications', sa.Column('phone_number', sa.String(length=50), nullable=True))
    op.add_column('ojt_applications', sa.Column('domicile', sa.String(length=100), nullable=True))
    op.add_column('ojt_applications', sa.Column('cv_url', sa.String(length=500), nullable=True))
    op.add_column('ojt_applications', sa.Column('portfolio_url', sa.String(length=500), nullable=True))


def downgrade():
    # Remove columns
    op.drop_column('ojt_applications', 'portfolio_url')
    op.drop_column('ojt_applications', 'cv_url')
    op.drop_column('ojt_applications', 'domicile')
    op.drop_column('ojt_applications', 'phone_number')
    op.drop_column('ojt_applications', 'full_name')
