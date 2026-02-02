from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0044'
down_revision = '0043'
branch_labels = None
depends_on = None


def upgrade():
    # Add whatsapp_number column to users table
    op.add_column('users', sa.Column('whatsapp_number', sa.String(50), nullable=True))


def downgrade():

    # Remove whatsapp_number column
    op.drop_column('users', 'whatsapp_number')