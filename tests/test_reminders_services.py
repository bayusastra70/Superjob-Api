import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.cron import check_reminders
from app.models.reminder import ReminderStatus, ReminderTask, ReminderTaskType
from app.services.reminder_service import get_pending_due_reminders


@pytest.mark.anyio
async def test_get_pending_due_reminders_filters_due_and_status(db_sessionmaker):
    now = datetime.now(timezone.utc)
    async with db_sessionmaker() as db:
        due_soon = ReminderTask(
            id=uuid.uuid4(),
            employer_id=uuid.uuid4(),
            task_title="Pending due soon",
            task_type=ReminderTaskType.candidate,
            redirect_url="/jobs/1/candidates",
            due_at=now + timedelta(minutes=5),
            status=ReminderStatus.pending,
        )
        due_late = ReminderTask(
            id=uuid.uuid4(),
            employer_id=due_soon.employer_id,
            task_title="Pending due later",
            task_type=ReminderTaskType.message,
            redirect_url="/messages/1",
            due_at=now + timedelta(minutes=120),
            status=ReminderStatus.pending,
        )
        done_due = ReminderTask(
            id=uuid.uuid4(),
            employer_id=due_soon.employer_id,
            task_title="Done not returned",
            task_type=ReminderTaskType.other,
            redirect_url="/",
            due_at=now + timedelta(minutes=10),
            status=ReminderStatus.done,
        )
        no_due = ReminderTask(
            id=uuid.uuid4(),
            employer_id=due_soon.employer_id,
            task_title="No due",
            task_type=ReminderTaskType.other,
            redirect_url="/",
            due_at=None,
            status=ReminderStatus.pending,
        )
        db.add_all([due_soon, due_late, done_due, no_due])
        await db.commit()

        results = await get_pending_due_reminders(db)

    titles = {r.task_title for r in results}
    assert titles == {"Pending due soon"}


@pytest.mark.anyio
async def test_cron_emits_due_reminders(monkeypatch, db_sessionmaker):
    emitted = []

    async def fake_emit(reminder):
        emitted.append(str(reminder.id))

    # Patch cron dependencies
    monkeypatch.setattr(check_reminders, "emit_reminder_due", fake_emit)
    monkeypatch.setattr(check_reminders, "SessionLocal", db_sessionmaker)

    now = datetime.now(timezone.utc)
    async with db_sessionmaker() as db:
        due_soon = ReminderTask(
            id=uuid.uuid4(),
            employer_id=uuid.uuid4(),
            task_title="Cron due soon",
            task_type=ReminderTaskType.job_update,
            redirect_url="/jobs/cron",
            due_at=now + timedelta(minutes=5),
            status=ReminderStatus.pending,
        )
        done_due = ReminderTask(
            id=uuid.uuid4(),
            employer_id=due_soon.employer_id,
            task_title="Cron done",
            task_type=ReminderTaskType.job_update,
            redirect_url="/jobs/cron",
            due_at=now + timedelta(minutes=5),
            status=ReminderStatus.done,
        )
        db.add_all([due_soon, done_due])
        await db.commit()

    await check_reminders.main()

    assert emitted == [str(due_soon.id)]
