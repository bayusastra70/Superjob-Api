
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0034'
down_revision = '0033'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update semua record dengan user_id = 9 dan user_agent dummy
    op.execute("""
        UPDATE job_views 
        SET user_id = 9, 
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        WHERE user_id IS NULL OR user_agent IS NULL
    """)
    
    # Optional: Tampilkan jumlah yang di-update
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT COUNT(*) FROM job_views"))
    count = result.scalar()
    print(f"✅ Updated {count} records in job_views table")


def downgrade() -> None:
    # Reset ke nilai NULL saat rollback
    op.execute("""
        UPDATE job_views 
        SET user_id = NULL, 
            user_agent = NULL
    """)
    print("✅ Reset user_id and user_agent to NULL")