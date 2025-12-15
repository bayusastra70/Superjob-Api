"""Cleanup role redundancy in activity_logs meta_data

Revision ID: 0003_cleanup_role_redundancy
Revises: 0002_seed_initial_data
Create Date: 2025-12-15 11:40:00.000000

This migration:
1. Copies role from user_role or associated_data.role to meta_data.role if missing
2. Removes redundant user_role field from meta_data
3. Removes redundant role field from meta_data.associated_data
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "0003_cleanup_role_redundancy"
down_revision = "0002_seed_initial_data"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Normalize role storage in activity_logs.meta_data:
    - Ensure meta_data.role exists (copy from user_role or associated_data.role if needed)
    - Remove user_role from meta_data
    - Remove role from associated_data
    """

    # Step 1: Copy role from user_role if meta_data.role is null/missing
    op.execute("""
    UPDATE activity_logs
    SET meta_data = jsonb_set(
        meta_data::jsonb,
        '{role}',
        COALESCE(
            meta_data::jsonb->'role',
            meta_data::jsonb->'user_role',
            meta_data::jsonb#>'{associated_data,role}',
            '"unknown"'::jsonb
        )
    )::json
    WHERE meta_data::jsonb->>'role' IS NULL
      AND (
          meta_data::jsonb->>'user_role' IS NOT NULL
          OR meta_data::jsonb#>>'{associated_data,role}' IS NOT NULL
      )
    """)

    # Step 2: Remove user_role from meta_data
    op.execute("""
    UPDATE activity_logs
    SET meta_data = (meta_data::jsonb - 'user_role')::json
    WHERE meta_data::jsonb ? 'user_role'
    """)

    # Step 3: Remove role from associated_data
    op.execute("""
    UPDATE activity_logs
    SET meta_data = jsonb_set(
        meta_data::jsonb,
        '{associated_data}',
        (meta_data::jsonb->'associated_data') - 'role'
    )::json
    WHERE meta_data::jsonb#>'{associated_data}' ? 'role'
    """)


def downgrade() -> None:
    """
    Restore redundant role fields for backward compatibility.
    This copies meta_data.role back to user_role and associated_data.role.
    """

    # Step 1: Re-add user_role from role
    op.execute("""
    UPDATE activity_logs
    SET meta_data = jsonb_set(
        meta_data::jsonb,
        '{user_role}',
        COALESCE(meta_data::jsonb->'role', '"unknown"'::jsonb)
    )::json
    WHERE meta_data::jsonb->>'role' IS NOT NULL
    """)

    # Step 2: Re-add role to associated_data
    op.execute("""
    UPDATE activity_logs
    SET meta_data = jsonb_set(
        meta_data::jsonb,
        '{associated_data,role}',
        COALESCE(meta_data::jsonb->'role', '"unknown"'::jsonb)
    )::json
    WHERE meta_data::jsonb ? 'associated_data'
      AND meta_data::jsonb->>'role' IS NOT NULL
    """)
