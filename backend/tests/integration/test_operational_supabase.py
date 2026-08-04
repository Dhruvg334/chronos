from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from supabase import create_client

pytestmark = pytest.mark.integration
PASSWORD = "ChronOS-local-operations-2026!"


def _config():
    if os.getenv("RUN_SUPABASE_INTEGRATION") != "1": pytest.skip("Set RUN_SUPABASE_INTEGRATION=1 to run local Supabase integration tests.")
    values = (os.getenv("SUPABASE_TEST_URL"), os.getenv("SUPABASE_TEST_ANON_KEY"), os.getenv("SUPABASE_TEST_SERVICE_ROLE_KEY"))
    if not all(values): pytest.skip("Local Supabase integration environment is incomplete.")
    return values


def test_atomic_limits_lifecycle_and_rls():
    url, anon_key, service_key = _config(); admin = create_client(url, service_key)
    users = []
    try:
        for label in ("alpha", "beta"):
            response = admin.auth.admin.create_user({"email": f"chronos.operations.{label}@example.com", "password": PASSWORD, "email_confirm": True})
            users.append(str(response.user.id))
        alpha = create_client(url, anon_key); alpha.auth.sign_in_with_password({"email": "chronos.operations.alpha@example.com", "password": PASSWORD})
        beta = create_client(url, anon_key); beta.auth.sign_in_with_password({"email": "chronos.operations.beta@example.com", "password": PASSWORD})
        alpha_id, beta_id = users

        first = admin.rpc("consume_usage_budget", {"p_user_id": alpha_id, "p_category": "model_calls", "p_user_limit": 1, "p_global_limit": 100, "p_units": 1}).execute().data
        denied = admin.rpc("consume_usage_budget", {"p_user_id": alpha_id, "p_category": "model_calls", "p_user_limit": 1, "p_global_limit": 100, "p_units": 1}).execute().data
        assert first["allowed"] is True and denied["allowed"] is False
        assert alpha.table("operational_audit_events").select("failure_code").execute().data[0]["failure_code"] == "rate_limited"
        assert beta.table("operational_audit_events").select("id").execute().data == []
        with pytest.raises(Exception): alpha.rpc("consume_usage_budget", {"p_user_id": alpha_id, "p_category": "mcp_calls", "p_user_limit": 1, "p_global_limit": 1, "p_units": 1}).execute()

        source_id = str(uuid.uuid4()); chunk_id = str(uuid.uuid4()); vector = [0.0] * 384
        ingested = admin.rpc("ingest_knowledge_source_transaction", {"p_user_id": alpha_id, "p_idempotency_key": f"ops-{uuid.uuid4()}", "p_source": {"id": source_id, "source_type": "note", "title": "Delete me", "checksum": "e" * 64}, "p_chunks": [{"id": chunk_id, "content": "owned", "embedding": vector, "token_count": 1, "position": 0}]}).execute().data
        assert ingested["status"] == "ready"
        with pytest.raises(Exception): beta.rpc("delete_knowledge_source_transaction", {"p_user_id": beta_id, "p_source_id": source_id}).execute()
        deleted = alpha.rpc("delete_knowledge_source_transaction", {"p_user_id": alpha_id, "p_source_id": source_id}).execute().data
        assert deleted == {"status": "deleted", "chunk_count": 1}
        assert admin.table("knowledge_chunks").select("id").eq("id", chunk_id).execute().data == []

        inventory = alpha.rpc("account_data_inventory", {"p_user_id": alpha_id}).execute().data
        assert "projects" in inventory
        with pytest.raises(Exception): alpha.rpc("account_data_inventory", {"p_user_id": beta_id}).execute()
        with pytest.raises(Exception): admin.rpc("delete_account_transaction", {"p_user_id": alpha_id, "p_confirmation": "wrong"}).execute()
        assert admin.auth.admin.get_user_by_id(alpha_id).user is not None
        admin.rpc("set_google_tokens", {"p_user_id": alpha_id, "p_google_email": "alpha@example.com", "p_access_token": "disposable-access", "p_refresh_token": "disposable-refresh", "p_token_uri": "https://oauth2.googleapis.com/token", "p_client_id": "local-test", "p_scopes": ["calendar.readonly"], "p_expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()}).execute()
        assert admin.table("google_connections").select("user_id").eq("user_id", alpha_id).execute().data
        result = admin.rpc("delete_account_transaction", {"p_user_id": alpha_id, "p_confirmation": "DELETE MY ACCOUNT"}).execute().data
        assert result["status"] == "deleted"
        assert admin.table("google_connections").select("user_id").eq("user_id", alpha_id).execute().data == []
        # A signed JWT remains cryptographically valid until expiry, but the deleted
        # owner has no rows and Auth no longer resolves the user for backend access.
        assert alpha.table("projects").select("id").execute().data == []
        with pytest.raises(Exception): alpha.auth.get_user()
        assert admin.auth.admin.get_user_by_id(beta_id).user is not None
        users.remove(alpha_id)
    finally:
        for user_id in users:
            try: admin.auth.admin.delete_user(user_id)
            except Exception: pass
