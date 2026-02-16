"""
Test Mobile Auth Redirect - Tests for the mobile OAuth bridge endpoint
Features tested:
- GET /api/auth/mobile-redirect with scheme param returns HTML that redirects to app deep link
- GET /api/auth/mobile-redirect without scheme defaults to 'amen' scheme
- POST /api/auth/login works with valid credentials
- POST /api/auth/google-callback returns 401 for invalid session
"""
import pytest
import requests
import os
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestMobileAuthRedirect:
    """Tests for mobile OAuth bridge endpoint"""

    def test_mobile_redirect_with_scheme_param(self):
        """GET /api/auth/mobile-redirect?scheme=amen should return HTML with correct scheme"""
        response = requests.get(f"{BASE_URL}/api/auth/mobile-redirect?scheme=amen")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Verify it returns HTML
        assert "text/html" in response.headers.get('content-type', ''), "Expected HTML response"
        
        # Verify HTML contains correct scheme redirect
        html = response.text
        assert "amen://auth-callback?session_id=" in html, "HTML should contain amen:// deep link"
        assert "window.location.href=" in html, "HTML should redirect via window.location.href"
        assert "Accesso in corso..." in html, "HTML should show loading message in Italian"
        
    def test_mobile_redirect_custom_scheme(self):
        """GET /api/auth/mobile-redirect?scheme=testapp should use custom scheme"""
        response = requests.get(f"{BASE_URL}/api/auth/mobile-redirect?scheme=testapp")
        assert response.status_code == 200
        
        html = response.text
        assert "testapp://auth-callback?session_id=" in html, "HTML should use custom scheme"
        
    def test_mobile_redirect_default_scheme(self):
        """GET /api/auth/mobile-redirect without scheme param should default to 'amen'"""
        response = requests.get(f"{BASE_URL}/api/auth/mobile-redirect")
        assert response.status_code == 200
        
        html = response.text
        assert "amen://auth-callback?session_id=" in html, "HTML should default to amen:// scheme"
        
    def test_mobile_redirect_html_structure(self):
        """Verify HTML structure has all required elements"""
        response = requests.get(f"{BASE_URL}/api/auth/mobile-redirect?scheme=amen")
        assert response.status_code == 200
        
        html = response.text
        
        # Check for loading spinner
        assert "class=\"loader\"" in html, "HTML should have loader element"
        
        # Check for error display element
        assert "id=\"err\"" in html, "HTML should have error display element"
        
        # Check for session_id extraction from hash
        assert "window.location.hash" in html, "HTML should read from hash fragment"
        assert "session_id" in html, "HTML should look for session_id"
        
        # Check for fallback message
        assert "Se l'app non si apre" in html or "Se l\\'app non si apre" in html, "HTML should have fallback message"
        assert "setTimeout" in html, "HTML should have timeout for fallback"
        
    def test_mobile_redirect_session_not_found_message(self):
        """Verify HTML shows error when no session_id in hash"""
        response = requests.get(f"{BASE_URL}/api/auth/mobile-redirect?scheme=amen")
        assert response.status_code == 200
        
        html = response.text
        # The else block shows this error when session_id is not found
        assert "Sessione non trovata" in html, "HTML should show 'session not found' message"


class TestAuthLogin:
    """Tests for regular login endpoint"""
    
    def test_login_with_valid_credentials(self):
        """POST /api/auth/login with valid credentials should return user and token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "testbible@cibospirituale.it",
                "password": "Test123!"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "user" in data, "Response should contain user object"
        assert "session_token" in data, "Response should contain session_token"
        assert data["user"]["email"] == "testbible@cibospirituale.it"
        
    def test_login_with_invalid_credentials(self):
        """POST /api/auth/login with invalid credentials should return 401"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "invalid@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data, "Error response should have detail field"


class TestGoogleCallback:
    """Tests for Google OAuth callback endpoint"""
    
    def test_google_callback_invalid_session(self):
        """POST /api/auth/google-callback with invalid session should return 401"""
        response = requests.post(
            f"{BASE_URL}/api/auth/google-callback",
            json={"session_id": "invalid-test-session-id"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data, "Error response should have detail field"
        
    def test_google_callback_missing_session_id(self):
        """POST /api/auth/google-callback without session_id should return 400"""
        response = requests.post(
            f"{BASE_URL}/api/auth/google-callback",
            json={}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data, "Error response should have detail field"
        assert "session_id" in data["detail"].lower() or "mancante" in data["detail"].lower()


class TestAuthMe:
    """Tests for /api/auth/me endpoint"""
    
    def test_auth_me_with_valid_session(self):
        """GET /api/auth/me with valid session should return user info"""
        # First login to get a valid session
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "testbible@cibospirituale.it",
                "password": "Test123!"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["session_token"]
        
        # Now test /auth/me with the token
        me_response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200, f"Expected 200, got {me_response.status_code}"
        
        data = me_response.json()
        assert data["email"] == "testbible@cibospirituale.it"
        
    def test_auth_me_without_session(self):
        """GET /api/auth/me without session should return 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
