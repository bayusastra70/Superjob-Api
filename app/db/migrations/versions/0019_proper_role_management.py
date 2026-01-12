"""Create proper role management system

Revision ID: 0019
Revises: 0018
Create Date: 2025-12-23

This migration creates a proper role-based access control (RBAC) system:
1. Creates roles table (replaces enum)
2. Creates permissions table  
3. Creates junction tables for many-to-many relationships
4. Migrates existing data from user_role enum
5. Adds proper foreign key constraints

NOTE: This version does NOT drop the old role column
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0019'
down_revision = '0018'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========== STEP 1: Create roles table ==========
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('name', sa.String(50), nullable=False, unique=True),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Create index
    op.create_index('ix_roles_name', 'roles', ['name'])
    op.create_index('ix_roles_is_active', 'roles', ['is_active'])
    
    # ========== STEP 2: Create permissions table ==========
    op.create_table(
        'permissions',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('code', sa.String(100), nullable=False, unique=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('module', sa.String(50), nullable=False),  # e.g., 'job', 'application', 'company'
        sa.Column('action', sa.String(50), nullable=False),  # e.g., 'create', 'read', 'update', 'delete'
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Create index
    op.create_index('ix_permissions_code', 'permissions', ['code'])
    op.create_index('ix_permissions_module', 'permissions', ['module'])
    op.create_index('ix_permissions_module_action', 'permissions', ['module', 'action'])
    
    # ========== STEP 3: Create role_permissions junction table ==========
    op.create_table(
        'role_permissions',
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.Column('granted_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('granted_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )
    
    # Create index
    op.create_index('ix_role_permissions_role_id', 'role_permissions', ['role_id'])
    op.create_index('ix_role_permissions_permission_id', 'role_permissions', ['permission_id'])
    
    # ========== STEP 4: Create user_roles junction table ==========
    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('assigned_by', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )
    
    # Create index
    op.create_index('ix_user_roles_user_id', 'user_roles', ['user_id'])
    op.create_index('ix_user_roles_role_id', 'user_roles', ['role_id'])
    op.create_index('ix_user_roles_is_active', 'user_roles', ['is_active'])
    
    # ========== STEP 5: Insert default system roles ==========
    # These match the previous enum values
    op.execute("""
        INSERT INTO roles (id, name, description, is_system, is_active) VALUES
        (1, 'admin', 'System Administrator with full access', true, true),
        (2, 'employer', 'Company employer who can post jobs and manage applications', true, true),
        (3, 'candidate', 'Job seeker who can apply for jobs', true, true),
        (4, 'hr_manager', 'HR Manager with hiring authority', true, true),
        (5, 'recruiter', 'Recruiter who can source candidates', true, true),
        (6, 'interviewer', 'Can conduct interviews and give feedback', true, true),
        (7, 'viewer', 'Read-only access for reporting', true, true)
        ON CONFLICT (name) DO NOTHING;
    """)
    
    # Reset sequence for roles
    op.execute("SELECT setval('roles_id_seq', (SELECT MAX(id) FROM roles))")
    
    # ========== STEP 6: Insert default permissions ==========
    # Common permissions for the system
    op.execute("""
        INSERT INTO permissions (id, code, name, description, module, action) VALUES
        -- User management permissions
        (1, 'user.create', 'Create User', 'Can create new users', 'user', 'create'),
        (2, 'user.read', 'View Users', 'Can view user profiles', 'user', 'read'),
        (3, 'user.update', 'Update User', 'Can update user information', 'user', 'update'),
        (4, 'user.delete', 'Delete User', 'Can delete users', 'user', 'delete'),
        
        -- Job management permissions
        (5, 'job.create', 'Create Job', 'Can create new job postings', 'job', 'create'),
        (6, 'job.read', 'View Jobs', 'Can view job postings', 'job', 'read'),
        (7, 'job.update', 'Update Job', 'Can update job postings', 'job', 'update'),
        (8, 'job.delete', 'Delete Job', 'Can delete job postings', 'job', 'delete'),
        (9, 'job.publish', 'Publish Job', 'Can publish job postings', 'job', 'publish'),
        
        -- Application management permissions
        (10, 'application.create', 'Create Application', 'Can apply for jobs', 'application', 'create'),
        (11, 'application.read', 'View Applications', 'Can view job applications', 'application', 'read'),
        (12, 'application.update', 'Update Application', 'Can update application status', 'application', 'update'),
        (13, 'application.delete', 'Delete Application', 'Can delete applications', 'application', 'delete'),
        
        -- Company management permissions
        (14, 'company.create', 'Create Company', 'Can create company profiles', 'company', 'create'),
        (15, 'company.read', 'View Companies', 'Can view company profiles', 'company', 'read'),
        (16, 'company.update', 'Update Company', 'Can update company information', 'company', 'update'),
        (17, 'company.delete', 'Delete Company', 'Can delete companies', 'company', 'delete'),
        
        -- Interview management permissions
        (18, 'interview.create', 'Create Interview', 'Can schedule interviews', 'interview', 'create'),
        (19, 'interview.read', 'View Interviews', 'Can view interview schedules', 'interview', 'read'),
        (20, 'interview.update', 'Update Interview', 'Can update interview details', 'interview', 'update'),
        (21, 'interview.delete', 'Delete Interview', 'Can cancel interviews', 'interview', 'delete'),
        
        -- Chat permissions
        (22, 'chat.send', 'Send Message', 'Can send chat messages', 'chat', 'send'),
        (23, 'chat.read', 'Read Messages', 'Can read chat messages', 'chat', 'read'),
        
        -- System permissions (admin only)
        (24, 'system.config', 'System Configuration', 'Can configure system settings', 'system', 'configure'),
        (25, 'system.reports', 'View Reports', 'Can view system reports', 'system', 'read'),
        (26, 'system.audit', 'Audit Logs', 'Can view audit logs', 'system', 'read')
        ON CONFLICT (code) DO NOTHING;
    """)
    
    # Reset sequence for permissions
    op.execute("SELECT setval('permissions_id_seq', (SELECT MAX(id) FROM permissions))")
    
    # ========== STEP 7: Assign permissions to roles ==========
    # Admin: All permissions
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT 1, id FROM permissions
        ON CONFLICT (role_id, permission_id) DO NOTHING;
    """)
    
    # Employer: Job and application management
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id) VALUES
        (2, 5), (2, 6), (2, 7), (2, 8), (2, 9),  -- Job permissions
        (2, 11), (2, 12), (2, 13),  -- Application permissions (read, update, delete)
        (2, 15), (2, 16),  -- Company permissions (read, update own company)
        (2, 18), (2, 19), (2, 20), (2, 21),  -- Interview permissions
        (2, 22), (2, 23)  -- Chat permissions
        ON CONFLICT (role_id, permission_id) DO NOTHING;
    """)
    
    # Candidate: Limited permissions
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id) VALUES
        (3, 6),  -- Job read
        (3, 10), (3, 11), (3, 13),  -- Application create, read, delete (own)
        (3, 15),  -- Company read
        (3, 19),  -- Interview read (own)
        (3, 22), (3, 23)  -- Chat permissions
        ON CONFLICT (role_id, permission_id) DO NOTHING;
    """)
    
    # ========== STEP 8: Migrate existing user roles ==========
    # Create mapping from old role values to new role IDs
    op.execute("""
        INSERT INTO user_roles (user_id, role_id, assigned_at)
        SELECT 
            u.id,
            CASE 
                WHEN u.role = 'admin'::user_role THEN 1
                WHEN u.role = 'employer'::user_role THEN 2
                WHEN u.role = 'candidate'::user_role THEN 3
                ELSE 3  -- Default to candidate
            END as role_id,
            COALESCE(u.updated_at, u.created_at, NOW())
        FROM users u
        ON CONFLICT (user_id, role_id) DO NOTHING;
    """)
    
    # ========== STEP 9: Keep the old role column but make it nullable ==========
    # Change the column to nullable since we're keeping it for backward compatibility
    op.alter_column('users', 'role', nullable=True)
    
    # ========== STEP 10: Add default_role column to users ==========
    op.add_column(
        'users',
        sa.Column('default_role_id', sa.Integer(), nullable=True)
    )
    
    # Set default role based on existing role or first assigned role
    op.execute("""
        UPDATE users u
        SET default_role_id = 
            CASE 
                WHEN u.role = 'admin'::user_role THEN 1
                WHEN u.role = 'employer'::user_role THEN 2
                WHEN u.role = 'candidate'::user_role THEN 3
                ELSE (
                    SELECT role_id 
                    FROM user_roles ur 
                    WHERE ur.user_id = u.id 
                    ORDER BY assigned_at 
                    LIMIT 1
                )
            END
    """)
    
    # Set default for any remaining NULLs
    op.execute("""
        UPDATE users u
        SET default_role_id = 3  -- candidate
        WHERE default_role_id IS NULL
    """)
    
    # Make column NOT NULL
    op.alter_column('users', 'default_role_id', nullable=False)
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_users_default_role_id',
        'users',
        'roles',
        ['default_role_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # ========== STEP 11: Log the migration completion ==========
    print("""
    Role management system has been migrated successfully!
    
    New tables created:
    - roles: System and custom roles
    - permissions: Granular permissions
    - role_permissions: Role-permission mapping
    - user_roles: User-role assignment
    
    Changes to existing tables:
    - users.role column kept for backward compatibility (now nullable)
    - users.default_role_id added for new RBAC system
    
    IMPORTANT: The old 'role' column is still present but nullable.
    Applications should gradually migrate to use the new user_roles table.
    
    Next steps for application:
    1. Update authentication logic to check user_roles table (primary) and role column (fallback)
    2. Update permission checking to use new system
    3. Update UI to manage roles and permissions
    4. Once migration is complete, create a new migration to drop the old role column
    """)


def downgrade() -> None:
    # ========== STEP 1: Remove default_role_id column ==========
    op.drop_constraint('fk_users_default_role_id', 'users', type_='foreignkey')
    op.drop_column('users', 'default_role_id')
    
    # ========== STEP 2: Make old role column NOT NULL again ==========
    # Set any NULL values to 'candidate' before making NOT NULL
    op.execute("UPDATE users SET role = 'candidate'::user_role WHERE role IS NULL")
    op.alter_column('users', 'role', nullable=False)
    
    # ========== STEP 3: Drop new RBAC tables ==========
    op.drop_table('user_roles')
    op.drop_table('role_permissions')
    op.drop_table('permissions')
    op.drop_table('roles')
    
    print("""
    RBAC system has been removed. Reverted to old enum-based role system.
    The 'role' column in users table is now NOT NULL again.
    """)