
from alembic import op


# revision identifiers, used by Alembic.
revision = '0038'
down_revision = '0037'
branch_labels = None
depends_on = None


def upgrade():
    # Update existing users with default profile picture
    op.execute("""
        UPDATE users 
        SET profile_picture = 'https://i.pravatar.cc/150'
        WHERE profile_picture IS NULL
    """)


def downgrade():
    # Tidak bisa rollback update data, tapi kita bisa kosongkan
    op.execute("""
        UPDATE users 
        SET profile_picture = NULL
        WHERE profile_picture = 'https://i.pravatar.cc/150'
    """)