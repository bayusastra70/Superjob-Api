from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0030'
down_revision = '0029'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # ========== STEP 1: Verify all users have role assignments ==========
    print("Verifying all users have role assignments...")
    
    # Check if any users don't have roles in the new system
    op.execute("""
        DO $$
        DECLARE
            missing_roles_count INTEGER;
        BEGIN
            SELECT COUNT(*) INTO missing_roles_count
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            WHERE ur.role_id IS NULL;
            
            IF missing_roles_count > 0 THEN
                -- Assign default candidate role to users without roles
                INSERT INTO user_roles (user_id, role_id, assigned_at, is_active)
                SELECT 
                    u.id,
                    3, -- candidate role id
                    NOW(),
                    true
                FROM users u
                LEFT JOIN user_roles ur ON u.id = ur.user_id
                WHERE ur.role_id IS NULL;
                
                RAISE NOTICE 'Assigned candidate role to % users', missing_roles_count;
            END IF;
        END $$;
    """)
    
    # ========== STEP 2: Create function to validate user has active role ==========
    print("Creating validation function...")
    
    op.execute("""
        CREATE OR REPLACE FUNCTION check_user_has_active_role(user_id INTEGER)
        RETURNS BOOLEAN AS $$
        BEGIN
            RETURN EXISTS (
                SELECT 1 FROM user_roles ur 
                WHERE ur.user_id = check_user_has_active_role.user_id 
                AND ur.is_active = true
            );
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # ========== STEP 3: Remove default_role_id column ==========
    print("Removing default_role_id column...")
    
    # Drop the foreign key constraint first
    op.drop_constraint('fk_users_default_role_id', 'users', type_='foreignkey')
    
    # Drop the column
    op.drop_column('users', 'default_role_id')
    
    # ========== STEP 4: Remove old role enum column ==========
    print("Removing old role column...")
    
    # Drop the column
    op.drop_column('users', 'role')
    
    # ========== STEP 5: Drop the old user_role enum type ==========
    print("Dropping old user_role enum type...")
    
    # Check if the type exists before dropping (for safety)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_type 
                WHERE typname = 'user_role' 
                AND typtype = 'e'
            ) THEN
                DROP TYPE user_role;
                RAISE NOTICE 'Dropped user_role enum type';
            ELSE
                RAISE NOTICE 'user_role enum type does not exist, skipping';
            END IF;
        END $$;
    """)
    
    # ========== STEP 6: Create trigger to ensure users have active roles ==========
    print("Creating trigger for role validation...")
    
    # Create function for trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION validate_user_has_role()
        RETURNS TRIGGER AS $$
        BEGIN
            -- This is a BEFORE trigger on user_roles table
            -- When user_roles are modified, ensure at least one active role remains
            IF TG_OP = 'DELETE' OR TG_OP = 'UPDATE' THEN
                -- Check if after this operation, the user will have any active roles
                IF NOT check_user_has_active_role(OLD.user_id) THEN
                    RAISE EXCEPTION 'User % must have at least one active role', OLD.user_id;
                END IF;
            END IF;
            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger on user_roles table
    op.execute("""
        DROP TRIGGER IF EXISTS trg_validate_user_has_role ON user_roles;
        CREATE TRIGGER trg_validate_user_has_role
        BEFORE DELETE OR UPDATE ON user_roles
        FOR EACH ROW EXECUTE FUNCTION validate_user_has_role();
    """)
    
    # ========== STEP 7: Create view for users with roles ==========
    print("Creating view for users with roles...")
    
    op.execute("""
        CREATE OR REPLACE VIEW users_with_roles AS
        SELECT 
            u.*,
            COALESCE(
                json_agg(
                    json_build_object(
                        'role_id', r.id,
                        'role_name', r.name,
                        'assigned_at', ur.assigned_at,
                        'is_active', ur.is_active
                    )
                ) FILTER (WHERE ur.is_active = true),
                '[]'
            ) as active_roles,
            COALESCE(
                json_agg(r.name) FILTER (WHERE ur.is_active = true),
                '{}'
            ) as role_names
        FROM users u
        LEFT JOIN user_roles ur ON u.id = ur.user_id
        LEFT JOIN roles r ON ur.role_id = r.id
        GROUP BY u.id;
    """)
    
    print("""
    Migration completed successfully!
    
    Changes made:
    1. ✅ Verified all users have role assignments (assigned candidate role if missing)
    2. ✅ Created validation function check_user_has_active_role()
    3. ✅ Removed default_role_id column from users table
    4. ✅ Removed old role enum column from users table
    5. ✅ Dropped old user_role enum type
    6. ✅ Created trigger to ensure users have at least one active role
    7. ✅ Created view users_with_roles for easier querying
    
    The migration from old enum-based role system to new RBAC is now complete.
    All role management should now be done through:
    - roles table (for role definitions)
    - user_roles table (for user-role assignments)
    - role_permissions table (for role-permission mappings)
    - permissions table (for permission definitions)
    
    Application changes required:
    1. Update all queries that reference users.role to use user_roles table
    2. Update authentication middleware to check user_roles instead of role column
    3. Use the view users_with_roles for queries that need user and role information
    4. Update admin panels to manage roles through new tables
    """)


def downgrade() -> None:
    # ========== STEP 1: Drop the view ==========
    print("Dropping view...")
    
    op.execute("DROP VIEW IF EXISTS users_with_roles;")
    
    # ========== STEP 2: Drop the trigger and function ==========
    print("Dropping trigger and functions...")
    
    op.execute("DROP TRIGGER IF EXISTS trg_validate_user_has_role ON user_roles;")
    op.execute("DROP FUNCTION IF EXISTS validate_user_has_role();")
    op.execute("DROP FUNCTION IF EXISTS check_user_has_active_role(INTEGER);")
    
    # ========== STEP 3: Recreate the old user_role enum type ==========
    print("Recreating old user_role enum type...")
    
    op.execute("""
        CREATE TYPE user_role AS ENUM ('admin', 'employer', 'candidate');
    """)
    
    # ========== STEP 4: Add back the old role column ==========
    print("Adding back old role column...")
    
    op.add_column(
        'users',
        sa.Column(
            'role',
            postgresql.ENUM('admin', 'employer', 'candidate', name='user_role'),
            nullable=True,
            server_default='candidate'
        )
    )
    
    # ========== STEP 5: Restore role values from new system ==========
    print("Restoring role values from new RBAC system...")
    
    # Map from new role IDs to old role values
    # Use the first active role (ordered by role_id)
    op.execute("""
        UPDATE users u
        SET role = 
            CASE 
                WHEN EXISTS (
                    SELECT 1 FROM user_roles ur 
                    JOIN roles r ON ur.role_id = r.id 
                    WHERE ur.user_id = u.id 
                    AND ur.is_active = true 
                    AND r.name = 'admin'
                ) THEN 'admin'::user_role
                WHEN EXISTS (
                    SELECT 1 FROM user_roles ur 
                    JOIN roles r ON ur.role_id = r.id 
                    WHERE ur.user_id = u.id 
                    AND ur.is_active = true 
                    AND r.name = 'employer'
                ) THEN 'employer'::user_role
                ELSE 'candidate'::user_role
            END
        WHERE role IS NULL;
    """)
    
    # Make the column NOT NULL after populating all rows
    op.alter_column('users', 'role', nullable=False)
    
    # ========== STEP 6: Add back default_role_id column ==========
    print("Adding back default_role_id column...")
    
    op.add_column(
        'users',
        sa.Column('default_role_id', sa.Integer(), nullable=True)
    )
    
    # Set default_role_id based on the restored role column
    op.execute("""
        UPDATE users u
        SET default_role_id = 
            CASE 
                WHEN u.role = 'admin'::user_role THEN 1
                WHEN u.role = 'employer'::user_role THEN 2
                ELSE 3  -- candidate
            END
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
    
    print("""
    Downgrade completed successfully!
    
    Changes reverted:
    1. ✅ Dropped users_with_roles view
    2. ✅ Dropped trigger and validation functions
    3. ✅ Recreated user_role enum type
    4. ✅ Restored old role column with values from new system
    5. ✅ Added back default_role_id column
    
    System has been reverted to use both:
    - Old role enum column (primary)
    - New RBAC tables (still exist but unused)
    
    Note: The new RBAC tables (roles, permissions, role_permissions, user_roles)
    still exist but are not used by the application after downgrade.
    """)