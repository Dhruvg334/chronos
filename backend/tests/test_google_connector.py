from app.integrations.adapters import GoogleCalendarConnector


def test_google_event_normalizes_recurring_timezone_and_cancellation():
    connector = GoogleCalendarConnector(is_configured=True)
    item = connector.normalize({"id":"e1","summary":"Team call","status":"cancelled","recurringEventId":"series","start":{"dateTime":"2026-08-05T16:00:00+05:30","timeZone":"Asia/Kolkata"},"end":{"dateTime":"2026-08-05T17:00:00+05:30"}})
    assert item.item_type == "calendar_event"
    assert item.metadata["timezone"] == "Asia/Kolkata"
    assert item.metadata["recurring_event_id"] == "series"
    assert item.deleted_at is not None
    assert connector.required_scopes == ("https://www.googleapis.com/auth/calendar.readonly",)
