"""rename motivation letter to cover letter

Revision ID: 0061
Revises: 0060
Create Date: 2026-02-19 20:25:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0061'
down_revision = '0060'
branch_labels = None
depends_on = None


def upgrade():
    # Rename motivation_letter to cover_letter
    op.alter_column('ojt_applications', 'motivation_letter', new_column_name='cover_letter')


def downgrade():
    # Rename cover_letter back to motivation_letter
    op.alter_column('ojt_applications', 'cover_letter', new_column_name='motivation_letter')
