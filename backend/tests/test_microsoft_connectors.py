from app.integrations.adapters import MicrosoftPlannerConnector, OutlookCalendarConnector


def test_outlook_and_planner_have_read_only_normalized_contracts():
    outlook = OutlookCalendarConnector(is_configured=True); outlook.set_fixture_rows([{"id":"e","title":"Review","occurred_at":"2026-08-05T10:00:00+05:30","due_at":"2026-08-05T11:00:00+05:30","timezone":"Asia/Kolkata"}])
    planner = MicrosoftPlannerConnector(is_configured=True); planner.set_fixture_rows([{"id":"t","title":"Release review","due_at":"2026-08-08T12:00:00Z","plan_id":"p","bucket":"Ready","assignees":["me"]}])
    assert outlook.sync("u", None).items[0].item_type == "calendar_event"
    assert planner.sync("u", None).items[0].metadata["bucket"] == "Ready"
    assert outlook.required_scopes == ("Calendars.Read",)
    assert "Tasks.Read" in planner.required_scopes
