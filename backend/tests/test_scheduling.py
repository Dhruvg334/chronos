from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
import pytest

client = TestClient(app)

@patch("app.api.v1.scheduling.run_scheduling_graph")
def test_plan_schedule_success(mock_run_graph):
    mock_run_graph.return_value = {
        "agent_run_id": "test_run_id",
        "proposals": [{"id": "p1"}, {"id": "p2"}]
    }
    
    response = client.post("/api/v1/scheduling/plan", headers={"Authorization": "Bearer mock_token"})
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["proposals_generated"] == 2
    assert response.json()["agent_run_id"] == "test_run_id"

@patch("app.api.v1.scheduling.supabase_client")
def test_get_proposals(mock_supabase):
    mock_execute = mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.order.return_value.execute
    mock_execute.return_value.data = [{"id": "prop1", "title": "Test Prop"}]
    
    response = client.get("/api/v1/scheduling/proposals", headers={"Authorization": "Bearer mock_token"})
    assert response.status_code == 200
    assert len(response.json()["proposals"]) == 1
    assert response.json()["proposals"][0]["id"] == "prop1"

@patch("app.api.v1.scheduling.approve_single_proposal")
def test_approve_proposal_success(mock_approve):
    mock_approve.return_value = {"id": "new_focus_block_1"}
    
    response = client.post("/api/v1/scheduling/proposals/prop1/approve", headers={"Authorization": "Bearer mock_token"})
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["focus_block"]["id"] == "new_focus_block_1"

@patch("app.api.v1.scheduling.supabase_client")
def test_reject_proposal_success(mock_supabase):
    mock_select = mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute
    mock_select.return_value.data = [{"status": "pending"}]
    
    response = client.post("/api/v1/scheduling/proposals/prop1/reject", headers={"Authorization": "Bearer mock_token"})
    assert response.status_code == 200
    assert response.json()["success"] is True

@patch("app.api.v1.scheduling.approve_single_proposal")
@patch("app.api.v1.scheduling.supabase_client")
def test_approve_all_proposals(mock_supabase, mock_approve):
    mock_select = mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute
    mock_select.return_value.data = [{"id": "p1"}, {"id": "p2"}]
    
    # Let p1 succeed, p2 fail
    def side_effect(user_id, prop_id):
        if prop_id == "p1":
            return {"id": "fb1"}
        else:
            raise ValueError("Overlap detected")
            
    mock_approve.side_effect = side_effect
    
    response = client.post("/api/v1/scheduling/proposals/approve-all", headers={"Authorization": "Bearer mock_token"})
    assert response.status_code == 200
    
    res_json = response.json()
    assert res_json["success"] is True
    assert len(res_json["applied"]) == 1
    assert res_json["applied"][0]["id"] == "fb1"
    assert len(res_json["skipped"]) == 1
    assert res_json["skipped"][0]["id"] == "p2"
    assert "Overlap" in res_json["skipped"][0]["reason"]
