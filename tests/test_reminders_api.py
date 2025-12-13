import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db
from app.main import app
from app.models.reminder import ReminderStatus


def _make_reminder_payload():
    return {
        "task_title": "Review candidates for Designer",
        "task_type": "candidate",
        "redirect_url": "/jobs/123/candidates",
        "job_id": str(uuid.uuid4()),
        "candidate_id": None,
        "due_at": None,
    }


@pytest.mark.anyio
async def test_create_reminder():
    employer_id = uuid.uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/employers/{employer_id}/reminders",
            json=_make_reminder_payload(),
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["employer_id"] == str(employer_id)
    assert data["status"] == ReminderStatus.pending.value
    assert data["task_title"] == "Review candidates for Designer"


@pytest.mark.anyio
async def test_update_reminder_forbidden_other_employer():
    owner_id = uuid.uuid4()
    other_id = uuid.uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create = await client.post(
            f"/employers/{owner_id}/reminders", json=_make_reminder_payload()
        )
        reminder_id = create.json()["id"]

        resp = await client.patch(
            f"/employers/{other_id}/reminders/{reminder_id}",
            json={"status": ReminderStatus.done.value},
        )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_list_reminders_pending_filter():
    employer_id = uuid.uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # create pending
        await client.post(
            f"/employers/{employer_id}/reminders", json=_make_reminder_payload()
        )
        # create then mark done
        create_done = await client.post(
            f"/employers/{employer_id}/reminders", json=_make_reminder_payload()
        )
        reminder_done_id = create_done.json()["id"]
        await client.patch(
            f"/employers/{employer_id}/reminders/{reminder_done_id}",
            json={"status": ReminderStatus.done.value},
        )

        resp_pending = await client.get(
            f"/employers/{employer_id}/reminders", params={"status": "pending"}
        )
        resp_all = await client.get(f"/employers/{employer_id}/reminders", params={"status": ""})

    assert resp_pending.status_code == 200
    pending_items = resp_pending.json()
    assert len(pending_items) == 1
    assert pending_items[0]["status"] == "pending"

    assert resp_all.status_code == 200
    assert len(resp_all.json()) == 2
