from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
import pytest

client = TestClient(app)

@patch("app.api.v1.google.get_authorization_url")
def test_get_auth_url(mock_get_url):
    mock_get_url.return_value = "https://accounts.google.com/o/oauth2/auth?mock=true"
    response = client.get("/api/v1/google/auth/url", headers={"Authorization": "Bearer mock_token"})
    assert response.status_code == 200
    assert response.json()["auth_url"] == "https://accounts.google.com/o/oauth2/auth?mock=true"
    mock_get_url.assert_called_once()

@patch("app.api.v1.google.exchange_code_for_token")
def test_auth_callback_success(mock_exchange):
    # Should redirect
    response = client.get("/api/v1/google/auth/callback?code=mockcode&state=mockuser", follow_redirects=False)
    assert response.status_code == 307
    assert "calendar_connected=true" in response.headers["location"]
    mock_exchange.assert_called_once_with(code="mockcode", state="mockuser")

@patch("app.api.v1.google.exchange_code_for_token")
def test_auth_callback_failure(mock_exchange):
    mock_exchange.side_effect = Exception("Auth failed")
    response = client.get("/api/v1/google/auth/callback?code=mockcode&state=mockuser", follow_redirects=False)
    assert response.status_code == 307
    assert "calendar_error=exchange_failed" in response.headers["location"]

@patch("app.api.v1.google.get_connection_status")
def test_connection_status(mock_get_status):
    mock_get_status.return_value = {"connected": True, "email": "test@gmail.com"}
    response = client.get("/api/v1/google/connection", headers={"Authorization": "Bearer mock_token"})
    assert response.status_code == 200
    assert response.json()["connected"] is True
    assert response.json()["email"] == "test@gmail.com"
    # Ensure no secrets leak
    assert "access_token" not in response.json()

@patch("app.api.v1.google.disconnect")
def test_disconnect(mock_disconnect):
    response = client.post("/api/v1/google/disconnect", headers={"Authorization": "Bearer mock_token"})
    assert response.status_code == 200
    assert response.json()["success"] is True
    mock_disconnect.assert_called_once()
