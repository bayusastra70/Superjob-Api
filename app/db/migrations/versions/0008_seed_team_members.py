"""Seed team_members data

Revision ID: 0008
Revises: 0007
Create Date: 2025-12-17
"""

from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========== INSERT TEAM_MEMBERS ==========
    # employer_id merujuk ke users.id: 8 = employer@superjob.com, 3 = tanaka@gmail.com
    # user_id sekarang wajib dan merujuk ke users.id
    op.execute("""
    INSERT INTO team_members (id, employer_id, user_id, role, is_active, created_at, updated_at) VALUES
    (1, 8, 8, 'admin', TRUE, '2025-12-01 09:00:00', '2025-12-01 09:00:00'),
    (8, 3, 3, 'admin', TRUE, '2025-12-01 09:00:00', '2025-12-01 09:00:00')
    ON CONFLICT (id) DO NOTHING;
    """)

    # Reset sequence untuk auto-increment
    op.execute(
        "SELECT setval('team_members_id_seq', (SELECT MAX(id) FROM team_members))"
    )


def downgrade() -> None:
    op.execute("DELETE FROM team_members")
