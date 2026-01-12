"""Remove redundant team_members table

Revision ID: 0020_remove_team_members
Revises: 0019
Create Date: 2025-12-23

This migration removes the redundant team_members table since:
1. New RBAC system (user_roles) can handle team management
2. Relationship can be managed through permissions and role assignments
3. Simplifies the database schema
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0020'
down_revision = '0019'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========== STEP 1: Check if we need to migrate any data ==========
    # Since team_members was newly created and likely only has 2 rows from seed,
    # we can safely drop it. But let's check and log first.
    
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT COUNT(*) FROM team_members"))
    count = result.scalar()
    
    print(f"Found {count} rows in team_members table")
    
    if count > 0:
        print("Sample team_members data:")
        result = conn.execute(sa.text("SELECT * FROM team_members LIMIT 5"))
        for row in result:
            print(f"  - ID: {row[0]}, Employer: {row[1]}, User: {row[2]}, Role: {row[3]}")
        
        print("\nNote: This data will be lost. If needed, migrate to user_roles table.")
        print("Example migration SQL:")
        print("""
            INSERT INTO user_roles (user_id, role_id, assigned_at, assigned_by, is_active)
            SELECT 
                tm.user_id,
                CASE tm.role
                    WHEN 'admin' THEN 1
                    WHEN 'hr_manager' THEN 4
                    WHEN 'recruiter' THEN 5
                    WHEN 'hiring_manager' THEN 5
                    WHEN 'viewer' THEN 7
                    ELSE 7
                END as role_id,
                tm.created_at,
                tm.employer_id,
                tm.is_active
            FROM team_members tm
            ON CONFLICT (user_id, role_id) DO NOTHING;
        """)
    
    # ========== STEP 2: Drop the table ==========
    op.drop_table('team_members')
    
    # ========== STEP 3: Drop the team_member_role enum type ==========
    op.execute('DROP TYPE IF EXISTS team_member_role')
    
    # ========== STEP 4: Update activity_logs if they reference team_member_updated ==========
    # The activity_type 'team_member_updated' is now obsolete
    # We can either:
    # 1. Leave it (enum values can't be removed easily in PostgreSQL)
    # 2. Or update references to a different type
    
    print("""
    team_members table has been removed.
    
    For team management functionality:
    1. Use user_roles table to assign roles to users
    2. Add 'employer_id' or 'company_id' to user_roles if needed for scoping
    3. Use permissions system for granular access control
    
    Example query to get team members for an employer:
    SELECT u.*, r.name as role_name 
    FROM user_roles ur
    JOIN users u ON ur.user_id = u.id
    JOIN roles r ON ur.role_id = r.id
    WHERE ur.assigned_by = :employer_id  -- or add employer_id column to user_roles
    AND ur.is_active = true;
    """)


def downgrade() -> None:
    # ========== STEP 1: Recreate team_member_role enum ==========
    # op.execute("""
    #     DO $$ 
    #     BEGIN 
    #         IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'team_member_role') THEN
    #             CREATE TYPE team_member_role AS ENUM ('admin', 'hr_manager', 'recruiter', 'hiring_manager', 'viewer');
    #         END IF;
    #     END $$;
    # """)
    
    # ========== STEP 2: Recreate team_members table ==========
    op.create_table(
        'team_members',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('employer_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column(
            'role',
            sa.Enum(
                'admin',
                'hr_manager',
                'recruiter',
                'hiring_manager',
                'viewer',
                name='team_member_role',
            ),
            nullable=False,
            server_default='viewer',
        ),
        sa.Column(
            'is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('ix_team_members_employer_id', 'team_members', ['employer_id'])
    op.create_index('ix_team_members_user_id', 'team_members', ['user_id'])
    
    # ========== STEP 3: Reinsert seed data ==========
    op.execute("""
        INSERT INTO team_members (id, employer_id, user_id, role, is_active, created_at, updated_at) VALUES
        (1, 8, 8, 'admin', TRUE, '2025-12-01 09:00:00', '2025-12-01 09:00:00'),
        (8, 3, 3, 'admin', TRUE, '2025-12-01 09:00:00', '2025-12-01 09:00:00')
        ON CONFLICT (id) DO NOTHING;
    """)
    
    # Reset sequence
    op.execute("SELECT setval('team_members_id_seq', (SELECT MAX(id) FROM team_members))")