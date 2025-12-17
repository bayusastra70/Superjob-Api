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
    # user_id juga merujuk ke users.id (bisa NULL jika belum terhubung ke user account)
    op.execute("""
    INSERT INTO team_members (id, employer_id, user_id, name, email, role, is_active, created_at, updated_at) VALUES
    (1, 8, 8, 'Employer 1', 'employer@superjob.com', 'admin', TRUE, '2025-12-01 09:00:00', '2025-12-01 09:00:00'),
    (2, 8, NULL, 'Sarah Johnson', 'sarah.johnson@superjob.com', 'hr_manager', TRUE, '2025-12-02 10:00:00', '2025-12-02 10:00:00'),
    (3, 8, NULL, 'Michael Chen', 'michael.chen@superjob.com', 'recruiter', TRUE, '2025-12-03 11:00:00', '2025-12-03 11:00:00'),
    (4, 8, NULL, 'Amanda Williams', 'amanda.w@superjob.com', 'recruiter', TRUE, '2025-12-04 09:30:00', '2025-12-04 09:30:00'),
    (5, 8, NULL, 'David Kim', 'david.kim@superjob.com', 'hiring_manager', TRUE, '2025-12-05 14:00:00', '2025-12-05 14:00:00'),
    (6, 8, NULL, 'Jessica Brown', 'jessica.b@superjob.com', 'viewer', TRUE, '2025-12-06 10:00:00', '2025-12-06 10:00:00'),
    (7, 8, NULL, 'Robert Taylor', 'robert.t@superjob.com', 'viewer', FALSE, '2025-12-07 08:00:00', '2025-12-15 17:00:00'),
    (8, 3, 3, 'Tanaka', 'tanaka@gmail.com', 'admin', TRUE, '2025-12-01 09:00:00', '2025-12-01 09:00:00'),
    (9, 3, NULL, 'Yuki Suzuki', 'yuki.suzuki@designco.com', 'hr_manager', TRUE, '2025-12-03 10:00:00', '2025-12-03 10:00:00'),
    (10, 3, NULL, 'Kenji Yamamoto', 'kenji.y@designco.com', 'recruiter', TRUE, '2025-12-05 11:00:00', '2025-12-05 11:00:00')
    ON CONFLICT (id) DO NOTHING;
    """)

    # Reset sequence untuk auto-increment
    op.execute(
        "SELECT setval('team_members_id_seq', (SELECT MAX(id) FROM team_members))"
    )


def downgrade() -> None:
    op.execute("DELETE FROM team_members")
