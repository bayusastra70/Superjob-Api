
import logging
import bcrypt
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.candidate_info import CandidateInfo
from app.schemas.user import UserUpdate, UserPasswordUpdate
from app.utils.storage import delete_vercel_blob_sync

logger = logging.getLogger(__name__)

def update_user_profile(db: Session, user_id: int, update_data: UserUpdate) -> Optional[User]:
    """
    Update user profile data (Non-password fields).
    
    Features:
    - Updates standard fields (full_name, phone).
    - Updates CV URL for candidates, removing old files if necessary.
    - Transactional updates ensuring data integrity.
    """
    # 1. Fetch User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    # 2. Update Standard Fields
    if update_data.full_name is not None:
        user.full_name = update_data.full_name
    if update_data.phone is not None:
        user.phone = update_data.phone

    # 3. Handle CV Update (Candidates Only)
    is_candidate = (user.default_role_id == 3) or (user.role == "candidate")
    if is_candidate and update_data.cv_url is not None:
        _handle_candidate_cv_update(db, user, update_data.cv_url)

    # 4. Commit Changes
    try:
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        logger.error(f"Profile update failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )

def _handle_candidate_cv_update(db: Session, user: User, new_cv_url: str):
    """
    Helper to safely update candidate CV.
    - Creates CandidateInfo if missing.
    - Deletes old file from storage if URL changes.
    - Updates DB record.
    """
    if not user.candidate_info:
        # Create new info if it doesn't exist
        new_info = CandidateInfo(user_id=user.id, cv_url=new_cv_url)
        db.add(new_info)
    else:
        # Check if URL actually changed before doing anything
        current_cv_url = user.candidate_info.cv_url
        if current_cv_url and current_cv_url != new_cv_url:
            try:
                # TODO: next step - we gonna use Solvera Storage API here
                # Synchronously delete the old file to clean up storage
                delete_vercel_blob_sync(current_cv_url)
                logger.info(f"Deleted old CV for user {user.id}")
            except Exception as e:
                # Log but don't block the update? 
                # Or block? Failsafe is to log error and continue to allow user update.
                logger.warning(f"Failed to delete old CV: {e}")

        user.candidate_info.cv_url = new_cv_url

def update_user_password(db: Session, user_id: int, password_data: UserPasswordUpdate) -> bool:
    """
    Update user password with security checks.

    Checks:
    - User existence.
    - Auth provider restriction (Google users cannot change password).
    - Current password verification (if one exists).
    
    Returns:
    - True on success.
    - Raises HTTPException on failure.
    """
    # 1. Fetch User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    # 2. Security Check: Google Users
    # Users authenticated via Google typically don't have a password to update
    # and should manage security via Google.
    if user.auth_provider == "google":
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Google users cannot update their password."
        )

    # 3. Verify Current Password
    # If the user has a password set, we MUST verify it.
    if user.password_hash:
        is_password_valid = bcrypt.checkpw(
            password_data.current_password.encode('utf-8'), 
            user.password_hash.encode('utf-8')
        )
        if not is_password_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )
    
    # 4. Hash & Set New Password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_data.new_password.encode('utf-8'), salt)
    user.password_hash = hashed.decode('utf-8')

    # 5. Commit
    try:
        db.add(user)  # Explicitly add to session for clarity
        db.commit()
        logger.info(f"Password updated for user {user_id}")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Password update failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )
