import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.anyio
async def test_create_job(db_sessionmaker):
    employer_id = uuid.uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/employers/{employer_id}/jobs",
            json={"title": "QA Engineer", "status": "published", "location": "Jakarta"},
        )

    assert resp.status_code == 201
    data = resp.json()
    assert data["employer_id"] == str(employer_id)
    assert data["title"] == "QA Engineer"
    assert data["status"] == "published"
