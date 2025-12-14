import uuid
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.job_posting import JobPosting, JobStatus
from app.services.job_scoring import compute_quality_score
from app.api.job_quality import _quality_cache


async def _create_job(db, **overrides) -> JobPosting:
    base_kwargs = dict(
        id=uuid.uuid4(),
        employer_id=uuid.uuid4(),
        title="Senior Backend Engineer",
        description="A" * 200,
        salary_min=10000000,
        salary_max=20000000,
        salary_currency="IDR",
        skills=["Python", "FastAPI", "PostgreSQL"],
        location="Jakarta",
        employment_type="full-time",
        experience_level="senior",
        education="Bachelor",
        benefits="Health insurance, allowance",
        contact_url="https://example.com/apply",
        status=JobStatus.published,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    base_kwargs.update(overrides)

    job = JobPosting(**base_kwargs)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@pytest.mark.anyio
async def test_get_quality_score_success(db_sessionmaker):
    async with db_sessionmaker() as db:
        job = await _create_job(db)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/jobs/{job.id}/quality-score")

    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] >= 85
    assert data["grade"] == "Excellent"
    assert data["details"]["title"] > 0
    assert isinstance(data["suggestions"], list)
    # With complete data, suggestions should be empty or minimal
    assert len(data["suggestions"]) == 0
    assert data["optimal"] is True


@pytest.mark.anyio
async def test_get_quality_score_insufficient_data(db_sessionmaker):
    async with db_sessionmaker() as db:
        job = await _create_job(db, salary_min=None, salary_max=None)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/jobs/{job.id}/quality-score")

    assert resp.status_code == 400
    detail = resp.json()["detail"]
    assert detail["message"] == "Data tidak cukup untuk menilai postingan"
    assert "Tambahkan rentang gaji" in detail["suggestions"]
    # No optimal flag on error response


@pytest.mark.anyio
async def test_get_quality_score_draft_returns_null(db_sessionmaker):
    async with db_sessionmaker() as db:
        job = await _create_job(db, status=JobStatus.draft)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/jobs/{job.id}/quality-score")

    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] is None
    assert data["grade"] is None
    assert data["message"] == "Job masih draft; skor tidak dihitung"
    assert "Tambahkan rentang gaji" not in data["suggestions"]
    assert data["optimal"] is False


@pytest.mark.anyio
async def test_compute_quality_score_thresholds():
    job = JobPosting(
        id=uuid.uuid4(),
        employer_id=uuid.uuid4(),
        title="Test",
        description="short desc",  # <80 chars
        salary_min=1,
        skills=["Python"],
        location="City",
        employment_type="contract",
        experience_level="mid",
        status=JobStatus.published,
    )

    result = compute_quality_score(job)
    # description <80 -> 0, skills 1 -> half of 15
    assert result.details["description"] == 0
    assert result.details["skills"] == 7.5
    assert result.grade in {"Good", "Low", "Excellent"}


@pytest.mark.anyio
async def test_quality_score_cached(monkeypatch, db_sessionmaker):
    async with db_sessionmaker() as db:
        job = await _create_job(db)

    transport = ASGITransport(app=app)
    call_count = {"count": 0}

    original = compute_quality_score

    def counting_compute(job_obj):
        call_count["count"] += 1
        return original(job_obj)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First call uses real compute
        resp1 = await client.get(f"/jobs/{job.id}/quality-score")
        assert resp1.status_code == 200

        # Patch to ensure cache is used (should not call compute again)
        monkeypatch.setattr("app.api.job_quality.compute_quality_score", counting_compute)
        resp2 = await client.get(f"/jobs/{job.id}/quality-score")

    assert resp2.status_code == 200
    assert call_count["count"] == 0  # cache hit


@pytest.mark.anyio
async def test_update_job_clears_cache(monkeypatch, db_sessionmaker):
    async with db_sessionmaker() as db:
        job = await _create_job(db, salary_min=None, salary_max=None)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get(f"/jobs/{job.id}/quality-score")  # populate cache

    call_count = {"count": 0}

    original = compute_quality_score

    def counting_compute(job_obj):
        call_count["count"] += 1
        return original(job_obj)

    monkeypatch.setattr("app.api.job_quality.compute_quality_score", counting_compute)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp_patch = await client.patch(
            f"/jobs/{job.id}",
            json={"salary_min": 1000, "salary_max": 2000},
        )
        assert resp_patch.status_code == 200

        # After update, cache should be invalidated so compute is called once
        assert call_count["count"] == 1
        # cache should be repopulated
        updated_job_id = uuid.UUID(resp_patch.json()["job_id"])
        assert updated_job_id in _quality_cache
