import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.api.routers.auth import auth

client = TestClient(app, raise_server_exceptions=False)

def test_google_auth_talent_new_user_success():
    """
    Test successful auto-registration via Google OAuth
    """
    mock_result = {
        "user": {
            "id": 1,
            "email": "new.user@gmail.com",
            "full_name": "New User",
            "role": "candidate"
        },
        "is_new_user": True
    }
    
    with patch.object(auth, "google_authenticate_talent", return_value=mock_result):
        response = client.post(
            "/auth/talent/google",
            json={"id_token": "valid-new-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "new.user@gmail.com"
        assert data["user"]["role"] == "candidate"

def test_google_auth_talent_existing_user_success():
    """
    Test successful login for existing talent user
    """
    mock_result = {
        "user": {
            "id": 2,
            "email": "existing.user@gmail.com",
            "full_name": "Existing User",
            "role": "candidate"
        },
        "is_new_user": False
    }
    
    with patch.object(auth, "google_authenticate_talent", return_value=mock_result):
        response = client.post(
            "/auth/talent/google",
            json={"id_token": "valid-existing-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "existing.user@gmail.com"
        assert data["user"]["role"] == "candidate"

def test_google_auth_talent_role_mismatch():
    """
    Test failure when a corporate user attempts to login via talent Google endpoint
    """
    mock_result = {"error": "ROLE_MISMATCH"}
    
    with patch.object(auth, "google_authenticate_talent", return_value=mock_result):
        response = client.post(
            "/auth/talent/google",
            json={"id_token": "corporate-token"}
        )
        
        assert response.status_code == 403
        data = response.json()
        # System uses BaseResponse format: {"code": 403, "is_success": False, "message": "...", "data": None}
        assert "Corporate" in data["message"]

def test_google_auth_talent_invalid_token():
    """
    Test failure with invalid Google ID token
    """
    with patch.object(auth, "google_authenticate_talent", return_value=None):
        response = client.post(
            "/auth/talent/google",
            json={"id_token": "invalid-token"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Gagal memproses login Google" in data["message"]

def test_google_auth_talent_inactive_user():
    """
    Test failure when user account is inactive or disabled
    """
    # Service returns None if user is found but inactive or registration fails
    with patch.object(auth, "google_authenticate_talent", return_value=None):
        response = client.post(
            "/auth/talent/google",
            json={"id_token": "inactive-user-token"}
        )
        
        assert response.status_code == 401
        assert "Gagal memproses login Google" in response.json()["message"]

def test_google_auth_talent_missing_email_in_token():
    """
    Test failure when Google ID token doesn't contain an email
    """
    with patch.object(auth, "google_authenticate_talent", return_value=None):
        response = client.post(
            "/auth/talent/google",
            json={"id_token": "no-email-token"}
        )
        
        assert response.status_code == 401
        assert "Gagal memproses login Google" in response.json()["message"]

def test_google_auth_talent_service_exception():
    """
    Test behavior when service layer raises an unexpected exception
    """
    with patch.object(auth, "google_authenticate_talent", side_effect=Exception("Database crash")):
        response = client.post(
            "/auth/talent/google",
            json={"id_token": "valid-token"}
        )
        
        # General exception handler should catch this and return 500
        assert response.status_code == 500
        assert "Internal Server Error" in response.json()["message"]
