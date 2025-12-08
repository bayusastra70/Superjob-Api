from datetime import datetime, timedelta, timezone
from typing import List

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.reminder import ReminderTask, ReminderStatus


async def get_pending_due_reminders(db: AsyncSession) -> List[ReminderTask]:
    """
    Fetch pending reminders whose due_at is within the configured threshold window
    (defaults to 60 minutes from now).
    """
    now = datetime.now(timezone.utc)
    threshold = now + timedelta(minutes=settings.reminder_deadline_minutes)

    stmt = (
        select(ReminderTask)
        .where(
            ReminderTask.status == ReminderStatus.pending,
            ReminderTask.due_at.isnot(None),
            ReminderTask.due_at <= threshold,
        )
        .order_by(ReminderTask.due_at.asc())
    )

    result = await db.execute(stmt)
    reminders = result.scalars().all()

    logger.info(
        "Checked pending reminders nearing deadline",
        count=len(reminders),
        window_minutes=settings.reminder_deadline_minutes,
    )
    return reminders
