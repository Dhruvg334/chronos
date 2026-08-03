from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.google_calendar_service import get_free_busy, sync_calendar_events
from app.services.google_oauth_service import get_valid_credentials


USER = "00000000-0000-0000-0000-000000000001"


class FakeCredentials:
    expired = False
    token = "access-secret"
    refresh_token = "refresh-secret"
    token_uri = "https://oauth2.googleapis.com/token"
    client_id = "client"
    scopes = ["https://www.googleapis.com/auth/calendar.readonly"]
    expiry = datetime.now(timezone.utc) + timedelta(hours=1)

    def __init__(self, **values):
        for key, value in values.items(): setattr(self, key, value)

    def refresh(self, _request):
        self.token = "refreshed-secret"
        self.expiry = datetime.now(timezone.utc) + timedelta(hours=1)


def vault_client():
    client = MagicMock()
    client.rpc.return_value.execute.return_value.data = [{"access_token": "access-secret", "refresh_token": "refresh-secret", "token_uri": "https://oauth2.googleapis.com/token", "client_id": "client", "scopes": ["https://www.googleapis.com/auth/calendar.readonly"], "expires_at": datetime.now(timezone.utc).isoformat()}]
    return client


def test_vault_credentials_are_retrieved_and_expired_token_is_refreshed_without_exposure():
    client = vault_client()
    with patch("app.services.google_oauth_service.supabase_client", client), patch("app.services.google_oauth_service.Credentials", FakeCredentials), patch("app.services.google_oauth_service.Request"):
        FakeCredentials.expired = True
        credentials = get_valid_credentials(USER)
    assert credentials is not None
    assert client.rpc.call_args_list[0].args[0] == "get_decrypted_google_tokens"
    assert client.rpc.call_args_list[-1].args[0] == "set_google_tokens"
    stored = client.rpc.call_args_list[-1].args[1]
    assert stored["p_refresh_token"] == ""


def test_revoked_or_failed_refresh_returns_no_credentials_and_logs_no_token(caplog):
    class Revoked(FakeCredentials):
        expired = True
        def refresh(self, _request): raise RuntimeError("provider rejected access-secret")
    client = vault_client()
    with patch("app.services.google_oauth_service.supabase_client", client), patch("app.services.google_oauth_service.Credentials", Revoked), patch("app.services.google_oauth_service.Request"):
        assert get_valid_credentials(USER) is None
    assert "access-secret" not in caplog.text


def test_event_sync_preserves_timezone_and_free_busy_is_read_only():
    event = {"id": "evt-1", "summary": "Team call", "start": {"dateTime": "2026-08-04T16:00:00+05:30"}, "end": {"dateTime": "2026-08-04T17:00:00+05:30"}}
    events_api = MagicMock()
    events_api.list.return_value.execute.return_value = {"items": [event]}
    freebusy_api = MagicMock()
    freebusy_api.query.return_value.execute.return_value = {"calendars": {"primary": {"busy": [{"start": event["start"]["dateTime"], "end": event["end"]["dateTime"]}]}}}
    service = MagicMock()
    service.events.return_value = events_api
    service.freebusy.return_value = freebusy_api
    database = MagicMock()
    database.table.return_value.upsert.return_value.execute.return_value = SimpleNamespace(data=[])
    database.table.return_value.update.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=[])
    with patch("app.services.google_calendar_service.get_valid_credentials", return_value=FakeCredentials()), patch("app.services.google_calendar_service.build", return_value=service), patch("app.services.google_calendar_service.supabase_client", database):
        assert sync_calendar_events(USER) is True
        busy = get_free_busy(USER, datetime.now(timezone.utc), datetime.now(timezone.utc) + timedelta(days=1))
    payload = database.table.return_value.upsert.call_args.args[0]
    assert payload["start_at"].endswith("+05:30")
    assert payload["is_chronos_created"] is False
    assert busy[0]["start"].endswith("+05:30")
    assert service.events().insert.call_count == 0
