import random
from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.job import Job, JobStatus


async def _create_job(db, **overrides) -> Job:
    job = Job(
        employer_id=overrides.get("employer_id", 999),
        title="Sample",
        description="A" * 200,
        status=overrides.get("status", JobStatus.published),
        created_at=overrides.get("created_at", datetime.now(timezone.utc)),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@pytest.mark.anyio
async def test_quick_actions_counts(db_sessionmaker):
    employer_id = random.randint(10000, 99999)
    async with db_sessionmaker() as db:
        await _create_job(db, employer_id=employer_id, status=JobStatus.published)
        await _create_job(
            db,
            employer_id=employer_id,
            status=JobStatus.published,
            created_at=datetime.now(timezone.utc) - timedelta(days=2),
        )
        await _create_job(db, employer_id=employer_id, status=JobStatus.draft)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            f"/employers/{employer_id}/dashboard/quick-actions",
            params={
                "last_viewed_job_post_at": datetime.now(timezone.utc)
                - timedelta(hours=12)
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["metrics"]["activeJobPosts"] == 2  # published jobs
    assert data["metrics"]["newJobPosts"] >= 1  # one within 12h window


@pytest.mark.anyio
async def test_quick_actions_no_items(db_sessionmaker):
    employer_id = random.randint(10000, 99999)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/employers/{employer_id}/dashboard/quick-actions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["metrics"] == {
        "activeJobPosts": 0,
        "totalApplicants": 0,
        "newApplicants": 0,
        "newMessages": 0,
        "newJobPosts": 0,
    }
    assert data["badges"] == {
        "newApplicants": False,
        "newMessages": False,
        "newJobPosts": False,
    }


@pytest.mark.anyio
async def test_mark_seen_resets_badge(db_sessionmaker):
    employer_id = random.randint(10000, 99999)
    async with db_sessionmaker() as db:
        await _create_job(db, employer_id=employer_id, status=JobStatus.published)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # initial fetch shows new job post
        resp1 = await client.get(f"/employers/{employer_id}/dashboard/quick-actions")
        assert resp1.status_code == 200
        assert resp1.json()["badges"]["newJobPosts"] is True

        # reset badge
        resp_reset = await client.patch(
            f"/employers/{employer_id}/dashboard/reset-badges",
            json={"items": ["newJobPosts"]},
        )
        assert resp_reset.status_code == 204

        # fetch again without params -> badge should drop to false due to seen timestamp
        resp2 = await client.get(f"/employers/{employer_id}/dashboard/quick-actions")
        assert resp2.status_code == 200
        assert resp2.json()["badges"]["newJobPosts"] is False


@pytest.mark.anyio
async def test_mark_seen_validation(db_sessionmaker):
    employer_id = random.randint(10000, 99999)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.patch(
            f"/employers/{employer_id}/dashboard/reset-badges",
            json={"items": []},
        )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_quick_actions_performance(db_sessionmaker):
    employer_id = random.randint(10000, 99999)
    async with db_sessionmaker() as db:
        await _create_job(db, employer_id=employer_id, status=JobStatus.published)

    transport = ASGITransport(app=app)
    start = datetime.now(timezone.utc)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(5):
            resp = await client.get(f"/employers/{employer_id}/dashboard/quick-actions")
            assert resp.status_code == 200
    elapsed_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000
    # Light load check: average < 200ms per request in test env (5 requests -> <1000ms total)
    assert elapsed_ms < 1000
