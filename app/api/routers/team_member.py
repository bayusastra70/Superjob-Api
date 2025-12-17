from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
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


@router.get(
    "",
    response_model=TeamMemberListResponse,
    summary="List Team Members",
    description="Mendapatkan daftar semua aggota tim.",
)
async def list_team_members(
    employer_id: int = Path(..., description="ID Employer"),
    limit: int = Query(20, ge=1, le=100, description="Jumlah data yang diambil"),
    offset: int = Query(0, ge=0, description="Offset data yang diambil"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get all team members for an employer"""
    # Count total
    total = await db.scalar(
        select(func.count())
        .select_from(TeamMember)
        .where(TeamMember.employer_id == employer_id)
    )

    # Get members
    stmt = (
        select(TeamMember)
        .where(TeamMember.employer_id == employer_id)
        .order_by(TeamMember.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    members = result.scalars().all()

    return TeamMemberListResponse(items=members, total=total or 0)


@router.post(
    "",
    response_model=TeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Team Member",
    description="""
    Menambahkan anggota tim baru.
    
    **Roles yang tersedia:**
    - `admin` - Full access
    - `hr_manager` - HR Manager
    - `recruiter` - Recruiter
    - `hiring_manager` - Hiring Manager
    - `viewer` - View only
    
    **⚠️ Membutuhkan Authorization Token!**
    """,
)
async def add_team_member(
    request: Request,
    employer_id: int = Path(..., description="ID Employer"),
    member_data: TeamMemberCreate = ...,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Add a new team member"""
    try:
        # Check if email already exists for this employer
        existing = await db.scalar(
            select(TeamMember).where(
                TeamMember.employer_id == employer_id,
                TeamMember.email == member_data.email,
            )
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team member with this email already exists",
            )
        # Create new team member
        new_member = TeamMember(
            employer_id=employer_id,
            user_id=member_data.user_id,
            name=member_data.name,
            email=member_data.email,
            role=member_data.role.value,
        )
        db.add(new_member)
        await db.commit()
        await db.refresh(new_member)
        # Log activity
        activity_log_service.log_team_member_updated(
            employer_id=employer_id,
            member_name=member_data.name,
            action="added",
            new_role=member_data.role.value,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            role="employer",
        )
        return new_member
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
    description="Update data anggota tim (nama, email, role, status aktif).",
)
async def update_team_member(
    request: Request,
    employer_id: int = Path(..., description="ID Employer"),
    member_id: int = Path(..., description="ID Team Member"),
    member_data: TeamMemberUpdate = ...,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Update team member"""
    member = await db.get(TeamMember, member_id)
    if not member or member.employer_id != employer_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found",
        )
    old_role = member.role
    updated = False
    # Update fields
    if member_data.name is not None:
        member.name = member_data.name
        updated = True
    if member_data.email is not None:
        member.email = member_data.email
        updated = True
    if member_data.role is not None:
        member.role = member_data.role.value
        updated = True
    if member_data.is_active is not None:
        member.is_active = member_data.is_active
        updated = True
    if updated:
        await db.commit()
        await db.refresh(member)
        # Determine action type
        action = (
            "role_changed"
            if member_data.role and member_data.role.value != old_role
            else "updated"
        )
        # Log activity
        activity_log_service.log_team_member_updated(
            employer_id=employer_id,
            member_name=member.name,
            action=action,
            new_role=member.role if member_data.role else None,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            role="employer",
        )
    return member


@router.delete(
    "/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove Team Member",
    description="Menghapus anggota dari tim.",
)
async def remove_team_member(
    request: Request,
    employer_id: int = Path(..., description="ID Employer"),
    member_id: int = Path(..., description="ID Team Member"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Remove team member"""
    member = await db.get(TeamMember, member_id)
    if not member or member.employer_id != employer_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found",
        )
    member_name = member.name
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
