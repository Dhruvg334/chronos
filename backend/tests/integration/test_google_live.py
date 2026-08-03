import os
from datetime import datetime, timedelta, timezone

import pytest

from app.services.google_calendar_service import get_free_busy, sync_calendar_events
from app.services.google_oauth_service import create_oauth_state, get_authorization_url, get_connection_status, get_valid_credentials, validate_oauth_state


@pytest.mark.integration
def test_real_google_read_only_connection_sync_and_free_busy():
    if os.getenv("RUN_GOOGLE_INTEGRATION") != "1":
        pytest.skip("RUN_GOOGLE_INTEGRATION=1 is required for the live Google test.")
    required = ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_OAUTH_STATE_SECRET", "GOOGLE_TEST_USER_ID", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        pytest.skip(f"Live Google configuration is missing: {', '.join(missing)}")
    user_id = os.environ["GOOGLE_TEST_USER_ID"]
    state = create_oauth_state(user_id)
    assert validate_oauth_state(state) == user_id
    auth_url = get_authorization_url(user_id)
    assert "calendar.readonly" in auth_url and "state=" in auth_url
    status = get_connection_status(user_id)
    if not status.get("connected"):
        pytest.skip("The configured Google test user has no Vault-backed authorization to validate.")
    credentials = get_valid_credentials(user_id)
    assert credentials is not None and credentials.token
    assert sync_calendar_events(user_id, days_ahead=14) is True
    now = datetime.now(timezone.utc)
    busy = get_free_busy(user_id, now, now + timedelta(days=2))
    assert busy is not None
    assert all("start" in item and "end" in item for item in busy)
    safe_status = get_connection_status(user_id)
    assert "access_token" not in safe_status and "refresh_token" not in safe_status
