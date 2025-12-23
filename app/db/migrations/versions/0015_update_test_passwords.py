"""Update test users with proper password hashes

Revision ID: 0015_update_test_passwords
Revises: 0014_consolidate_job_postings_to_jobs
Create Date: 2025-12-22

This migration updates the password hashes for test users to match the documented
credentials in the authentication API documentation.

Test Credentials after this migration:
- admin@superjob.com / admin123 (role: admin)
- employer@superjob.com / employer123 (role: employer)
- tanaka@gmail.com / password123 (role: employer)
- candidate@superjob.com / candidate123 (role: candidate)
- john.doe@example.com / password123 (role: candidate)
- jane.smith@example.com / password123 (role: candidate)
- bob.wilson@example.com / password123 (role: candidate)
- alice.johnson@example.com / password123 (role: candidate)
- charlie.brown@example.com / password123 (role: candidate)
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0015_update_test_passwords"
down_revision = "0014"
branch_labels = None
depends_on = None

# Password hashes generated with bcrypt
# admin123
ADMIN_HASH = "$2b$12$f9RzSVZpTG4xPz4RROFVVuyyVCzMc6FQ89RJcE6Xs/Mh/naAjE7q."
# employer123
EMPLOYER_HASH = "$2b$12$L93s.9.32E8frY.LwK3jAOilEUKobrge8fR8H4f3W9PEBEwgI7azm"
# candidate123
CANDIDATE_HASH = "$2b$12$I/npmgSS7WdJu2V5ZTyUUO/PZQYW7MpEShA6ng2ODGGCrGAfrVuH2"
# password123
PASSWORD_HASH = "$2b$12$zFPsdBRo1j18l8lWly4.se7sOoIs.SbGGG8RNa5RvuQecPvjD4qKC"


def upgrade() -> None:
    """
    Update password hashes for test users to match documented credentials.
    """

    # Update admin password to 'admin123'
    op.execute(f"""
        UPDATE users 
        SET password_hash = '{ADMIN_HASH}', 
            updated_at = CURRENT_TIMESTAMP
        WHERE email = 'admin@superjob.com'
    """)

    # Update employer@superjob.com password to 'employer123'
    op.execute(f"""
        UPDATE users 
        SET password_hash = '{EMPLOYER_HASH}', 
            updated_at = CURRENT_TIMESTAMP
        WHERE email = 'employer@superjob.com'
    """)

    # Update tanaka@gmail.com password to 'password123'
    op.execute(f"""
        UPDATE users 
        SET password_hash = '{PASSWORD_HASH}', 
            updated_at = CURRENT_TIMESTAMP
        WHERE email = 'tanaka@gmail.com'
    """)

    # Update candidate@superjob.com password to 'candidate123'
    op.execute(f"""
        UPDATE users 
        SET password_hash = '{CANDIDATE_HASH}', 
            updated_at = CURRENT_TIMESTAMP
        WHERE email = 'candidate@superjob.com'
    """)

    # Update sample candidates with 'password123'
    op.execute(f"""
        UPDATE users 
        SET password_hash = '{PASSWORD_HASH}', 
            updated_at = CURRENT_TIMESTAMP
        WHERE email IN (
            'john.doe@example.com',
            'jane.smith@example.com',
            'bob.wilson@example.com',
            'alice.johnson@example.com',
            'charlie.brown@example.com'
        )
    """)

    print("✅ Test user passwords updated successfully!")
    print("   - admin@superjob.com -> admin123")
    print("   - employer@superjob.com -> employer123")
    print("   - tanaka@gmail.com -> password123")
    print("   - candidate@superjob.com -> candidate123")
    print("   - Sample candidates -> password123")


def downgrade() -> None:
    """
    Note: We cannot restore original passwords as they are irreversibly hashed.
    This is a one-way migration for test data purposes.
    """
    # No-op: Cannot restore original password hashes
    pass
