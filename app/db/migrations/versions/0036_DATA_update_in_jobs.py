from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0036'
down_revision = '0035'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update status, published_at, dan expired_at sesuai kondisi
    op.execute("""
        UPDATE jobs
        SET
            status = CASE
                WHEN status = 'open' THEN 'published'
                ELSE status
            END,

            published_at = CASE
                WHEN status IN ('open', 'published') THEN NOW()
                ELSE published_at
            END,

            expired_at = CASE
                WHEN status = 'closed' THEN NOW()
                ELSE NOW() + INTERVAL '1 month'
            END
    """)
    
    # Optional: Tampilkan jumlah yang di-update
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT COUNT(*) FROM jobs"))
    count = result.scalar()
    print(f"✅ Updated {count} records in jobs table")


def downgrade() -> None:
    # Rollback perubahan status (hanya untuk 'published' yang sebelumnya 'open')
    op.execute("""
        UPDATE jobs
        SET
            status = CASE
                WHEN status = 'published' THEN 'open'
                ELSE status
            END,
            published_at = NULL,
            expired_at = NULL
        WHERE status = 'published'
    """)
    print("✅ Rollback jobs status changes")