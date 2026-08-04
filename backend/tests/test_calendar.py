from fastapi.testclient import TestClient
import pytest

from app.api.dependencies import get_connector_registry, get_repositories
from app.integrations.fake import FakeConnector
from app.integrations.registry import ConnectorRegistry
from app.main import app
from tests.fakes import MemoryIntegrations, MemoryPlanning, repositories

client = TestClient(app)
USER = "00000000-0000-0000-0000-000000000001"


class CalendarFake(FakeConnector):
    def __init__(self, *, fail=False, busy="unset"):
        super().__init__("google_calendar"); self.fail=fail; self.busy=busy
    def sync(self, *args, **kwargs):
        if self.fail: raise TimeoutError("timeout")
        return super().sync(*args, **kwargs)
    def free_busy(self, *args, **kwargs):
        if self.busy == "unset": raise RuntimeError("unavailable")
        return self.busy


@pytest.fixture(autouse=True)
def cleanup():
    yield
    app.dependency_overrides.clear()


def configure(connector, planning=None):
    integrations=MemoryIntegrations(); integrations.create_connection(USER, {"id":"connection","provider":"google_calendar","status":"connected","sync_cursor":None,"sync_metadata":{}})
    app.dependency_overrides[get_repositories] = lambda: repositories(planning=planning or MemoryPlanning(), integrations=integrations)
    app.dependency_overrides[get_connector_registry] = lambda: ConnectorRegistry([connector])


def test_sync_calendar_success():
    configure(CalendarFake())
    response = client.post("/api/v1/calendar/sync", headers={"Authorization": "Bearer mock_token"})
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_sync_calendar_failure():
    configure(CalendarFake(fail=True))
    response = client.post("/api/v1/calendar/sync", headers={"Authorization": "Bearer mock_token"})
    assert response.status_code == 500


def test_get_events():
    planning=MemoryPlanning(events=[{"id":"1","title":"Test Event","user_id":USER,"start_at":"2026-08-03T10:00:00Z","end_at":"2099-08-03T11:00:00Z"}])
    configure(CalendarFake(), planning)
    response = client.get("/api/v1/calendar/events", headers={"Authorization": "Bearer mock_token"})
    assert response.status_code == 200
    assert response.json()["events"][0]["title"] == "Test Event"


def test_fetch_free_busy_success():
    configure(CalendarFake(busy=[{"start":"2026-06-29T10:00:00Z","end":"2026-06-29T11:00:00Z"}]))
    response = client.post("/api/v1/calendar/free-busy", headers={"Authorization":"Bearer mock_token"}, json={"time_min":"2026-06-29T00:00:00Z","time_max":"2026-06-29T23:59:59Z"})
    assert response.status_code == 200
    assert len(response.json()["busy_blocks"]) == 1


def test_fetch_free_busy_failure():
    configure(CalendarFake())
    response = client.post("/api/v1/calendar/free-busy", headers={"Authorization":"Bearer mock_token"}, json={"time_min":"2026-06-29T00:00:00Z","time_max":"2026-06-29T23:59:59Z"})
    assert response.status_code == 500
