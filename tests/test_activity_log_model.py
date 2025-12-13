import pytest

from app.models.activity_log import ActivityLog, ActivityType


def test_activity_log_redirect_url_cta():
    log = ActivityLog(
        employer_id="emp-1",
        type=ActivityType.NEW_APPLICANT,
        title="Pelamar baru",
        meta_data={"cta": "/jobs/1/applications/2"},
    )
    assert log.redirect_url() == "/jobs/1/applications/2"


def test_activity_log_redirect_url_fallback_none():
    log = ActivityLog(
        employer_id="emp-1",
        type=ActivityType.NEW_MESSAGE,
        title="Pesan baru",
        meta_data={"body": "Hello"},
    )
    assert log.redirect_url() is None


@pytest.mark.anyio
async def test_activity_log_model_columns(db_engine):
    # Ensure table exists in metadata; create_all already ran in fixture.
    from sqlalchemy import inspect

    inspector = inspect(db_engine.sync_engine)
    columns = {col["name"] for col in inspector.get_columns("activity_logs")}
    expected = {
        "id",
        "employer_id",
        "type",
        "title",
        "subtitle",
        "meta_data",
        "job_id",
        "applicant_id",
        "message_id",
        "timestamp",
        "is_read",
    }
    assert expected.issubset(columns)
