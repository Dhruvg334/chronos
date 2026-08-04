from __future__ import annotations

import os
import uuid

import pytest
from supabase import create_client

pytestmark = pytest.mark.integration
PASSWORD = "ChronOS-integrations-local-2026!"


def config():
    if os.getenv("RUN_SUPABASE_INTEGRATION") != "1": pytest.skip("Set RUN_SUPABASE_INTEGRATION=1 for local integration security tests.")
    values = (os.getenv("SUPABASE_TEST_URL"), os.getenv("SUPABASE_TEST_ANON_KEY"), os.getenv("SUPABASE_TEST_SERVICE_ROLE_KEY"))
    if not all(values): pytest.skip("Local Supabase integration configuration is incomplete.")
    return values


@pytest.fixture(scope="module")
def clients():
    url, anon, service = config(); admin = create_client(url, service); users=[]; browser=[]
    for label in ("alpha", "beta"):
        email=f"chronos.integrations.{label}@example.com"; response=admin.auth.admin.create_user({"email":email,"password":PASSWORD,"email_confirm":True}); users.append(str(response.user.id))
        client=create_client(url,anon); client.auth.sign_in_with_password({"email":email,"password":PASSWORD}); browser.append(client)
    yield admin,browser[0],browser[1],users[0],users[1]
    for user_id in users: admin.auth.admin.delete_user(user_id)


def test_integration_rls_column_grants_and_approval_rollback(clients):
    admin, alpha, beta, alpha_id, beta_id = clients
    project=admin.table("projects").insert({"user_id":beta_id,"title":"Beta private","description":"","status":"active","colour":"accent"}).execute().data[0]
    connection=admin.table("integration_connections").insert({"user_id":alpha_id,"provider":"gmail","status":"connected","granted_scopes":["gmail.readonly"],"external_account_reference":"alpha","token_reference":"vault:private"}).execute().data[0]
    item=admin.table("integration_items").insert({"user_id":alpha_id,"connection_id":connection["id"],"provider":"gmail","external_id":"m1","item_type":"email","title":"Auth regression deadline","content_summary":"Finish by tomorrow","checksum":"a"*64,"metadata":{"untrusted_content":True}}).execute().data[0]
    proposal=admin.table("integration_action_proposals").insert({"user_id":alpha_id,"connection_id":connection["id"],"integration_item_id":item["id"],"action_type":"create_task","safe_summary":"Email appears to contain a deadline","validated_payload":{"untrusted_content":True},"status":"pending","approval_requirement":"explicit","idempotency_key":str(uuid.uuid4())}).execute().data[0]

    safe_columns="id,user_id,provider,status,granted_scopes,external_account_reference,connected_at,last_success_at,last_error_at,last_error_code,created_at,updated_at"
    assert len(alpha.table("integration_connections").select(safe_columns).execute().data)==1
    assert beta.table("integration_connections").select(safe_columns).execute().data==[]
    assert beta.table("integration_items").select("id,title").execute().data==[]
    assert beta.table("integration_action_proposals").select("id,safe_summary").execute().data==[]
    with pytest.raises(Exception): alpha.table("integration_connections").select("token_reference").execute()
    with pytest.raises(Exception): beta.table("integration_items").update({"title":"stolen"}).eq("id",item["id"]).execute()

    with pytest.raises(Exception): alpha.rpc("approve_integration_proposal_transaction", {"p_user_id":alpha_id,"p_proposal_id":proposal["id"],"p_action_type":"create_outcome","p_project_id":project["id"]}).execute()
    assert admin.table("integration_action_proposals").select("status").eq("id",proposal["id"]).single().execute().data["status"]=="pending"
    assert admin.table("outcomes").select("id").eq("user_id",alpha_id).eq("title","Auth regression deadline").execute().data==[]

    approved=alpha.rpc("approve_integration_proposal_transaction", {"p_user_id":alpha_id,"p_proposal_id":proposal["id"],"p_action_type":"create_task","p_project_id":None}).execute().data
    replay=alpha.rpc("approve_integration_proposal_transaction", {"p_user_id":alpha_id,"p_proposal_id":proposal["id"],"p_action_type":"create_task","p_project_id":None}).execute().data
    assert approved["status"]=="approved" and approved["idempotent_replay"] is False
    assert replay["idempotent_replay"] is True
    assert len(admin.table("commitments").select("id").eq("user_id",alpha_id).eq("title","Auth regression deadline").execute().data)==1
