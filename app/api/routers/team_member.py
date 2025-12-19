from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
import logging

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
from app.services.activity_log_service import activity_log_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/employers/{employer_id}/team-members",
    tags=["Team Members"],
)


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
    - `items`: List team members dengan data user (name, email dari tabel users)
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
    """Get all team members for an employer.

    Args:
        employer_id: ID employer yang team members-nya ingin diambil.
        limit: Jumlah maksimal data yang dikembalikan.
        offset: Offset untuk pagination.
        db: Database session.
        current_user: User yang sedang login.

    Returns:
        TeamMemberListResponse dengan list team members dan total count.

    Raises:
        HTTPException 403: Jika user tidak memiliki akses ke employer ini.
    """
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
        .options(joinedload(TeamMember.user))  # Eager load user data
        .where(TeamMember.employer_id == employer_id)
        .order_by(TeamMember.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    members = (
        result.scalars().unique().all()
    )  # unique() untuk menghindari duplikat dari joinedload

    return TeamMemberListResponse(items=members, total=total or 0)


@router.post(
    "",
    response_model=TeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Team Member",
    description="""
    Menambahkan anggota tim baru.
    
    **Authorization:**
    User harus menjadi team member dari employer yang diminta.
    
    **Roles yang tersedia:**
    - `admin` - Full access
    - `hr_manager` - HR Manager
    - `recruiter` - Recruiter
    - `hiring_manager` - Hiring Manager
    - `trainer` - Trainer only
    
    **Request Body:**
    - `user_id`: ID user yang akan ditambahkan (wajib, harus sudah ada di tabel users)
    - `role`: Role untuk team member ini (default: viewer)
    """,
)
async def add_team_member(
    request: Request,
    employer_id: int = Path(..., description="ID Employer"),
    member_data: TeamMemberCreate = ...,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> TeamMemberResponse:
    """Add a new team member.

    Args:
        request: HTTP request untuk mendapatkan IP dan user agent.
        employer_id: ID employer tempat menambahkan team member.
        member_data: Data team member baru (user_id dan role).
        db: Database session.
        current_user: User yang sedang login.

    Returns:
        TeamMemberResponse dengan data team member yang baru dibuat.

    Raises:
        HTTPException 403: Jika user tidak memiliki akses ke employer ini.
        HTTPException 400: Jika user_id sudah menjadi team member.
        HTTPException 404: Jika user_id tidak ditemukan.
    """
    try:
        # Authorization check
        await require_employer_access(db, current_user.id, employer_id)

        # Verify user exists
        from app.models.user import User

        user = await db.get(User, member_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {member_data.user_id} not found",
            )

        # Check if user is already a team member for this employer
        existing = await db.scalar(
            select(TeamMember).where(
                TeamMember.employer_id == employer_id,
                TeamMember.user_id == member_data.user_id,
            )
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This user is already a team member",
            )

        # Create new team member
        new_member = TeamMember(
            employer_id=employer_id,
            user_id=member_data.user_id,
            role=member_data.role.value,
        )
        db.add(new_member)
        await db.commit()

        # Refresh dengan eager load user untuk response
        await db.refresh(new_member)
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
    Update data anggota tim.
    
    **Authorization:**
    User harus menjadi team member dari employer yang diminta.
    
    **Fields yang bisa diupdate:**
    - `role`: Role baru untuk team member
    - `is_active`: Status aktif team member
    
    **Note:** Name dan email diambil dari tabel users dan tidak bisa diupdate di sini.
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
    """Update team member.

    Args:
        request: HTTP request untuk mendapatkan IP dan user agent.
        employer_id: ID employer pemilik team member.
        member_id: ID team member yang akan diupdate.
        member_data: Data update (role dan/atau is_active).
        db: Database session.
        current_user: User yang sedang login.

    Returns:
        TeamMemberResponse dengan data team member yang sudah diupdate.

    Raises:
        HTTPException 403: Jika user tidak memiliki akses ke employer ini.
        HTTPException 404: Jika team member tidak ditemukan.
    """
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

    # Update fields (only role and is_active are updatable)
    if member_data.role is not None:
        member.role = member_data.role.value
        updated = True
    if member_data.is_active is not None:
        member.is_active = member_data.is_active
        updated = True

    if updated:
        await db.commit()
        await db.refresh(member)

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
        member_name = member.user.username if member.user else f"User #{member.user_id}"

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
    """Remove team member.

    Args:
        request: HTTP request untuk mendapatkan IP dan user agent.
        employer_id: ID employer pemilik team member.
        member_id: ID team member yang akan dihapus.
        db: Database session.
        current_user: User yang sedang login.

    Returns:
        None (HTTP 204 No Content).

    Raises:
        HTTPException 403: Jika user tidak memiliki akses ke employer ini.
        HTTPException 404: Jika team member tidak ditemukan.
        HTTPException 400: Jika user mencoba menghapus dirinya sendiri.
    """
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
