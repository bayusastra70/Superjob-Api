import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.reminder import ReminderTask, ReminderStatus
from app.schemas.reminder import ReminderCreate, ReminderUpdate, ReminderResponse

router = APIRouter(prefix="/employers/{employer_id}/reminders", tags=["reminders"])


@router.post("", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    employer_id: uuid.UUID,
    payload: ReminderCreate,
    db: AsyncSession = Depends(get_db),
) -> ReminderResponse:
    reminder = ReminderTask(
        employer_id=employer_id,
        **payload.model_dump(),
    )

    db.add(reminder)
    try:
        await db.commit()
        await db.refresh(reminder)
    except SQLAlchemyError as exc:
        await db.rollback()
        logger.exception(
            "Failed to create reminder task",
            exc=exc,
            employer_id=employer_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create reminder task",
        )

    return reminder


@router.patch(
    "/{reminder_id}",
    response_model=ReminderResponse,
    status_code=status.HTTP_200_OK,
)
async def update_reminder(
    employer_id: uuid.UUID,
    reminder_id: uuid.UUID,
    payload: ReminderUpdate,
    db: AsyncSession = Depends(get_db),
) -> ReminderResponse:
    reminder = await db.get(ReminderTask, reminder_id)

    if reminder is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found"
        )

    if reminder.employer_id != employer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to modify this reminder",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(reminder, field, value)

    # Auto-hide behavior: if status moves to done/ignored, reminder stops showing on FE.
    if reminder.status in {ReminderStatus.done, ReminderStatus.ignored}:
        logger.debug(
            "Reminder status changed to terminal state; reminder will be hidden",
            reminder_id=str(reminder_id),
            status=reminder.status.value,
        )

    try:
        await db.commit()
        await db.refresh(reminder)
    except SQLAlchemyError as exc:
        await db.rollback()
        logger.exception(
            "Failed to update reminder task",
            exc=exc,
            reminder_id=reminder_id,
            employer_id=employer_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update reminder task",
        )

    return reminder
