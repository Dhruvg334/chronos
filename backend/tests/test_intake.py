import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.intake import IntakeResponse, ExtractedCommitment, ExtractedTask
from uuid import uuid4

client = TestClient(app)

@pytest.fixture
def mock_supabase():
    with patch("app.api.v1.intake.supabase_client") as mock:
        yield mock

@pytest.fixture
def mock_gemini():
    with patch("app.api.v1.intake.gemini_service") as mock:
        yield mock

def test_intake_process_success(mock_gemini, mock_supabase):
    mock_run_id = str(uuid4())
    
    with patch("app.api.v1.intake.create_agent_run", return_value=mock_run_id):
        mock_gemini.extract_structured.return_value = IntakeResponse(
            agent_run_id=mock_run_id,
            drafts=[],
            questions=[]
        )
        
        response = client.post("/api/v1/ai/intake", json={"text": "Hello world"})
        assert response.status_code == 200
        assert response.json()["agent_run_id"] == mock_run_id

def test_approve_empty(mock_supabase):
    # Empty approvals should 400
    response = client.post("/api/v1/ai/intake/approve", json={
        "agent_run_id": str(uuid4()),
        "approved_drafts": []
    })
    assert response.status_code == 400

def test_approve_success(mock_supabase):
    draft = {
        "title": "Do a thing",
        "type": "task",
        "estimated_minutes": 30,
        "importance": 3,
        "flexibility": 3,
        "confidence_score": 0.9,
        "tasks": [],
        "missing_fields": []
    }
    mock_supabase.table().insert().execute.return_value = MagicMock()
    
    with patch("app.api.v1.intake.AgentTraceLogger"):
        response = client.post("/api/v1/ai/intake/approve", json={
            "agent_run_id": str(uuid4()),
            "approved_drafts": [draft]
        })
        assert response.status_code == 200
        assert response.json()["count"] == 1
