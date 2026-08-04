import asyncio

from app.services import readiness


def test_readiness_is_bounded_and_safe_when_database_is_missing(monkeypatch):
    readiness._cache = None
    monkeypatch.setattr(readiness.settings, "SUPABASE_URL", "")
    monkeypatch.setattr(readiness.settings, "SUPABASE_SERVICE_ROLE_KEY", "")
    report = asyncio.run(readiness.readiness_report())
    assert report["status"] == "not_ready"
    assert report["dependencies"]["database"]["state"] == "configuration_missing"
    assert "environment" not in report
    assert "provider" not in report["dependencies"]["model"]


def test_detailed_status_requires_caller_context_but_exposes_no_identifiers(monkeypatch):
    readiness._cache = None
    monkeypatch.setattr(readiness.settings, "SUPABASE_URL", "")
    monkeypatch.setattr(readiness.settings, "SUPABASE_SERVICE_ROLE_KEY", "")
    result = asyncio.run(readiness.detailed_operational_status("private-user-id"))
    assert result["components"]["background_processing"] == "inline_bounded"
    assert "private-user-id" not in str(result)
