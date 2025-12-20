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
    
    **Ada 2 mode:**
    1. **Tambah user yang sudah ada**: Berikan `user_id` saja
    2. **Buat user baru + tambahkan ke tim**: Berikan `username`, `email`, `password` (user_id kosong)
    
    **Authorization:**
    User harus menjadi team member dari employer yang diminta.
    
    **Roles yang tersedia:**
    - `admin` - Full access
    - `hr_manager` - HR Manager
    - `recruiter` - Recruiter
    - `hiring_manager` - Hiring Manager
    - `trainer` - Trainer
    
    **Request Body:**
    - `user_id`: ID user yang sudah ada (optional)
    - `username`: Username (wajib jika buat user baru)
    - `full_name`: Nama lengkap (optional)
    - `email`: Email (wajib jika buat user baru)
    - `password`: Password (wajib jika buat user baru)
    - `role`: Role untuk team member (default: trainer)
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

        user = None

        # Case 1: User ID provided - use existing user
        if member_data.user_id:
            user = await db.get(User, member_data.user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with id {member_data.user_id} not found",
                )

        # Case 2: No user_id - create new user
        else:
            # Validate required fields for new user
            if not member_data.username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username is required when creating a new user",
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

            # Check if username already exists
            existing_username = await db.scalar(
                select(User).where(User.username == member_data.username)
            )
            if existing_username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User with username {member_data.username} already exists",
                )

            # Create new user
            user = User(
                username=member_data.username,
                full_name=member_data.full_name,
                email=member_data.email,
                password_hash=hash_password(member_data.password),
                is_active=True,
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
    
    **Authorization:**
    User harus menjadi team member dari employer yang diminta.
    
    **Fields yang bisa diupdate:**
    - `role`: Role baru untuk team member
    - `is_active`: Status aktif team member
    - `username`: Username user (di tabel users)
    - `full_name`: Nama lengkap user (di tabel users)
    - `email`: Email user (di tabel users)
    - `password`: Password baru (akan di-hash)
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
            if member_data.username is not None:
                # Check if new username conflicts
                if member_data.username != user.username:
                    existing = await db.scalar(
                        select(User).where(
                            User.username == member_data.username, User.id != user.id
                        )
                    )
                    if existing:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Username {member_data.username} already taken",
                        )
                    user.username = member_data.username
                    updated = True

            if member_data.full_name is not None:
                user.full_name = member_data.full_name
                updated = True

            if member_data.email is not None:
                # Check if new email conflicts
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
