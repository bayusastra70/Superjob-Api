from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
import logging
from passlib.context import CryptContext

from app.api.deps import get_db
from app.core.security import get_current_user
from app.schemas.user import UserResponse
from app.schemas.team_member import (
    TeamMemberCreate,
    TeamMemberUpdate,
    TeamMemberResponse,
    TeamMemberListResponse,
)
from app.models.team_member import TeamMember
from app.models.user import User
from app.services.activity_log_service import activity_log_service

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(
    prefix="/employers/{employer_id}/team-members",
    tags=["Team Members"],
)


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)


async def check_employer_access(
    db: AsyncSession,
    user_id: int,
    employer_id: int,
) -> bool:
    """
    Memeriksa apakah user memiliki akses ke employer tertentu.
    User dianggap memiliki akses jika dia adalah team member dari employer tersebut.
    """
    stmt = select(TeamMember).where(
        TeamMember.employer_id == employer_id,
        TeamMember.user_id == user_id,
        TeamMember.is_active.is_(True),
    )
    result = await db.scalar(stmt)
    return result is not None


async def require_employer_access(
    db: AsyncSession,
    user_id: int,
    employer_id: int,
) -> None:
    """
    Memastikan user memiliki akses ke employer. Raise HTTPException jika tidak.
    """
    has_access = await check_employer_access(db, user_id, employer_id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this employer's resources",
        )


@router.get(
    "",
    response_model=TeamMemberListResponse,
    summary="List Team Members",
    description="""
    Mendapatkan daftar semua anggota tim.
    
    **Authorization:**
    User harus menjadi team member dari employer yang diminta.
    
    **Response:**
    - `items`: List team members dengan data user (username, full_name, email dari tabel users)
    - `total`: Total jumlah team members
    """,
)
async def list_team_members(
    employer_id: int = Path(..., description="ID Employer"),
    limit: int = Query(20, ge=1, le=100, description="Jumlah data yang diambil"),
    offset: int = Query(0, ge=0, description="Offset data yang diambil"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> TeamMemberListResponse:
    """Get all team members for an employer."""
    # Authorization check
    await require_employer_access(db, current_user.id, employer_id)

    # Count total
    total = await db.scalar(
        select(func.count())
        .select_from(TeamMember)
        .where(TeamMember.employer_id == employer_id)
    )

    # Get members with user data
    stmt = (
        select(TeamMember)
        .options(joinedload(TeamMember.user))
        .where(TeamMember.employer_id == employer_id)
        .order_by(TeamMember.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    members = result.scalars().unique().all()

    return TeamMemberListResponse(items=members, total=total or 0)


@router.post(
    "",
    response_model=TeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Team Member",
    description="""
    Menambahkan anggota tim baru.
    
    **Design Reference:** "Add New Member" dialog
    
    **Ada 2 mode:**
    1. **Tambah user yang sudah ada**: Berikan `user_id` saja
    2. **Buat user baru + tambahkan ke tim**: Berikan `name`, `email`, `password` (user_id kosong)
    
    **Authorization:**
    User harus login sebagai Corporate (employer/admin) dan menjadi team member dari employer.
    
    **Company ID:**
    User baru akan otomatis mendapatkan `company_id` yang sama dengan user yang menambahkannya.
    Jika user existing ditambahkan dan belum punya `company_id`, maka akan diupdate.
    
    **Roles yang tersedia:**
    - `admin` - Full access
    - `hr_manager` - HR Manager
    - `recruiter` - Recruiter
    - `hiring_manager` - Hiring Manager
    - `trainer` - Trainer
    
    **Request Body:**
    - `name`: Nama lengkap (wajib jika buat user baru)
    - `phone`: Nomor telepon (optional)
    - `email`: Email (wajib jika buat user baru)
    - `role`: Role untuk team member (default: trainer)
    - `password`: Password (wajib jika buat user baru)
    """,
)
async def add_team_member(
    request: Request,
    employer_id: int = Path(..., description="ID Employer"),
    member_data: TeamMemberCreate = ...,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> TeamMemberResponse:
    """Add a new team member (with existing user or create new user)."""
    try:
        # Authorization check
        await require_employer_access(db, current_user.id, employer_id)

        # Get current user's company_id to inherit to new members
        current_user_db = await db.get(User, current_user.id)
        company_id = current_user_db.company_id if current_user_db else None

        user = None

        # Case 1: User ID provided - use existing user
        if member_data.user_id:
            user = await db.get(User, member_data.user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with id {member_data.user_id} not found",
                )
            # Update existing user's company_id if not set
            if user.company_id is None and company_id is not None:
                user.company_id = company_id

        # Case 2: No user_id - create new user
        else:
            # Validate required fields for new user
            if not member_data.name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Name is required when creating a new user",
                )
            if not member_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email is required when creating a new user",
                )
            if not member_data.password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Password is required when creating a new user",
                )

            # Check if email already exists
            existing_user = await db.scalar(
                select(User).where(User.email == member_data.email)
            )
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User with email {member_data.email} already exists",
                )

            # Generate username from email (sebelum @)
            base_username = member_data.email.split("@")[0]
            username = base_username

            # Check if username already exists, add suffix if needed
            counter = 1
            while await db.scalar(select(User).where(User.username == username)):
                username = f"{base_username}{counter}"
                counter += 1

            # Create new user with employer role and same company_id
            user = User(
                username=username,
                full_name=member_data.name,
                phone=member_data.phone,
                email=member_data.email,
                password_hash=hash_password(member_data.password),
                role="employer",  # Team members are always employer role
                is_active=True,
                company_id=company_id,  # Inherit company_id from current_user
            )
            db.add(user)
            await db.flush()  # Get ID but don't commit yet

        # Check if user is already a team member for this employer
        existing_member = await db.scalar(
            select(TeamMember).where(
                TeamMember.employer_id == employer_id,
                TeamMember.user_id == user.id,
            )
        )
        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This user is already a team member",
            )

        # Create new team member
        new_member = TeamMember(
            employer_id=employer_id,
            user_id=user.id,
            role=member_data.role.value,
        )
        db.add(new_member)
        await db.commit()

        # Refresh dengan eager load user untuk response
        stmt = (
            select(TeamMember)
            .options(joinedload(TeamMember.user))
            .where(TeamMember.id == new_member.id)
        )
        result = await db.execute(stmt)
        new_member = result.scalars().first()

        # Log activity
        activity_log_service.log_team_member_updated(
            employer_id=employer_id,
            member_name=user.username,
            action="added",
            new_role=member_data.role.value,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            role="employer",
        )

        return TeamMemberResponse.model_validate(new_member)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error adding team member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add team member",
        )


@router.put(
    "/{member_id}",
    response_model=TeamMemberResponse,
    summary="Update Team Member",
    description="""
    Update data anggota tim dan juga data user-nya.
    
    **Design Reference:** "Update Member" dialog
    
    **Authorization:**
    User harus login sebagai Corporate (employer/admin) dan menjadi team member dari employer.
    
    **Fields yang bisa diupdate:**
    - `name`: Nama lengkap
    - `phone`: Nomor telepon
    - `email`: Email
    - `role`: Role (admin, hr_manager, recruiter, hiring_manager, trainer)
    - `is_active`: Member active? (toggle)
    - `password`: Password baru (optional)
    """,
)
async def update_team_member(
    request: Request,
    employer_id: int = Path(..., description="ID Employer"),
    member_id: int = Path(..., description="ID Team Member"),
    member_data: TeamMemberUpdate = ...,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> TeamMemberResponse:
    """Update team member and optionally the associated user data."""
    try:
        # Authorization check
        await require_employer_access(db, current_user.id, employer_id)

        # Get member with user data
        stmt = (
            select(TeamMember)
            .options(joinedload(TeamMember.user))
            .where(TeamMember.id == member_id)
        )
        result = await db.execute(stmt)
        member = result.scalars().first()

        if not member or member.employer_id != employer_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team member not found",
            )

        old_role = member.role
        updated = False

        # Update team member fields
        if member_data.role is not None:
            member.role = member_data.role.value
            updated = True
        if member_data.is_active is not None:
            member.is_active = member_data.is_active
            updated = True

        # Update user fields if provided
        user = member.user
        if user:
            # Update name (full_name in database)
            if member_data.name is not None:
                user.full_name = member_data.name
                updated = True

            # Update phone
            if member_data.phone is not None:
                user.phone = member_data.phone
                updated = True

            # Update email with conflict check
            if member_data.email is not None:
                if member_data.email != user.email:
                    existing = await db.scalar(
                        select(User).where(
                            User.email == member_data.email, User.id != user.id
                        )
                    )
                    if existing:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Email {member_data.email} already taken",
                        )
                    user.email = member_data.email
                    updated = True

            # Update password
            if member_data.password is not None:
                user.password_hash = hash_password(member_data.password)
                updated = True

        if updated:
            await db.commit()

            # Re-fetch dengan user data untuk response
            result = await db.execute(stmt)
            member = result.scalars().first()

            # Determine action type
            action = (
                "role_changed"
                if member_data.role and member_data.role.value != old_role
                else "updated"
            )

            # Get username untuk logging
            member_name = (
                member.user.username if member.user else f"User #{member.user_id}"
            )

            # Log activity
            activity_log_service.log_team_member_updated(
                employer_id=employer_id,
                member_name=member_name,
                action=action,
                new_role=member.role if member_data.role else None,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                role="employer",
            )

        return TeamMemberResponse.model_validate(member)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating team member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update team member",
        )


@router.delete(
    "/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove Team Member",
    description="""
    Menghapus anggota dari tim.
    
    **Authorization:**
    User harus menjadi team member dari employer yang diminta.
    
    **Note:** User tidak bisa menghapus dirinya sendiri.
    """,
)
async def remove_team_member(
    request: Request,
    employer_id: int = Path(..., description="ID Employer"),
    member_id: int = Path(..., description="ID Team Member"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> None:
    """Remove team member."""
    # Authorization check
    await require_employer_access(db, current_user.id, employer_id)

    # Get member with user data
    stmt = (
        select(TeamMember)
        .options(joinedload(TeamMember.user))
        .where(TeamMember.id == member_id)
    )
    result = await db.execute(stmt)
    member = result.scalars().first()

    if not member or member.employer_id != employer_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found",
        )

    # Prevent self-deletion
    if member.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove yourself from the team",
        )

    # Get username untuk logging sebelum delete
    member_name = member.user.username if member.user else f"User #{member.user_id}"

    await db.delete(member)
    await db.commit()

    # Log activity
    activity_log_service.log_team_member_updated(
        employer_id=employer_id,
        member_name=member_name,
        action="removed",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        role="employer",
    )

    return None
