"""Add phone field to users table with invalid default values

Revision ID: 0012
Revises: 0011
Create Date: 2024-12-19

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision = '0012'
down_revision = '0011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tambahkan kolom phone ke tabel users dengan nullable=True
    op.add_column(
        'users',
        sa.Column('phone', sa.String(20), nullable=True)
    )
    
    # Update semua record yang ada dengan nilai default yang tidak valid
    # Gunakan kombinasi string yang jelas bukan nomor telepon
    conn = op.get_bind()
    
    # Query untuk mendapatkan semua user IDs
    result = conn.execute(text("SELECT id FROM users"))
    user_ids = [row[0] for row in result]
    
    # Update setiap user dengan "phone number" yang tidak valid
    for user_id in user_ids:
        # Format: "INVALID_USER_{ID}" - jelas bukan nomor telepon
        invalid_phone = f"628000000{user_id}"
        conn.execute(
            text("UPDATE users SET phone = :phone WHERE id = :id"),
            {"phone": invalid_phone, "id": user_id}
        )



def downgrade() -> None:
    # Hapus kolom phone dari tabel users
    op.drop_column('users', 'phone')