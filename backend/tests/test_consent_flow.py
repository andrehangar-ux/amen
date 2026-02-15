"""
Test cases for Terms & Conditions consent flow.
Tests the mandatory T&C acceptance after login.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://amen-corrections.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "testbible@cibospirituale.it"
TEST_PASSWORD = "Test123!"

class TestConsentFlow:
    """Tests for consent/T&C endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: login and get token for each test"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("session_token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_consent_status_requires_auth(self):
        """GET /api/consent/status should require authentication"""
        response = requests.get(f"{BASE_URL}/api/consent/status")
        assert response.status_code == 401, "Endpoint should require auth"
    
    def test_consent_status_returns_boolean(self):
        """GET /api/consent/status should return accepted status"""
        response = requests.get(
            f"{BASE_URL}/api/consent/status",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "accepted" in data, "Response should contain 'accepted' field"
        assert isinstance(data["accepted"], bool), "accepted should be boolean"
    
    def test_withdraw_consent(self):
        """DELETE /api/consent/withdraw should revoke consent"""
        response = requests.delete(
            f"{BASE_URL}/api/consent/withdraw",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True, "Withdraw should succeed"
    
    def test_consent_status_false_after_withdraw(self):
        """After withdraw, consent status should be false"""
        # First withdraw
        requests.delete(f"{BASE_URL}/api/consent/withdraw", headers=self.headers)
        
        # Check status
        response = requests.get(
            f"{BASE_URL}/api/consent/status",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["accepted"] == False, "Consent should be false after withdraw"
    
    def test_accept_consent(self):
        """POST /api/consent/accept should accept terms"""
        # First withdraw to ensure clean state
        requests.delete(f"{BASE_URL}/api/consent/withdraw", headers=self.headers)
        
        # Accept terms
        response = requests.post(
            f"{BASE_URL}/api/consent/accept?version=1.0",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True, "Accept should succeed"
        assert data.get("version") == "1.0", "Version should be returned"
        assert "document_hash" in data, "Should return document hash"
        assert "timestamp" in data, "Should return timestamp"
    
    def test_consent_status_true_after_accept(self):
        """After accept, consent status should be true"""
        # First withdraw
        requests.delete(f"{BASE_URL}/api/consent/withdraw", headers=self.headers)
        
        # Accept
        requests.post(
            f"{BASE_URL}/api/consent/accept?version=1.0",
            headers=self.headers
        )
        
        # Check status
        response = requests.get(
            f"{BASE_URL}/api/consent/status",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["accepted"] == True, "Consent should be true after accept"
        assert data.get("version") == "1.0", "Version should be returned"
        assert "accepted_at" in data, "Should return accepted_at timestamp"
    
    def test_accept_requires_version(self):
        """POST /api/consent/accept should require version parameter"""
        response = requests.post(
            f"{BASE_URL}/api/consent/accept",
            headers=self.headers
        )
        # FastAPI returns 422 for missing required query params
        assert response.status_code == 422, "Should fail without version"
    
    def test_full_consent_flow(self):
        """Full flow: withdraw -> check (false) -> accept -> check (true)"""
        # Step 1: Withdraw
        withdraw_resp = requests.delete(
            f"{BASE_URL}/api/consent/withdraw",
            headers=self.headers
        )
        assert withdraw_resp.status_code == 200
        
        # Step 2: Check status (should be false)
        status_resp_1 = requests.get(
            f"{BASE_URL}/api/consent/status",
            headers=self.headers
        )
        assert status_resp_1.status_code == 200
        assert status_resp_1.json()["accepted"] == False
        
        # Step 3: Accept
        accept_resp = requests.post(
            f"{BASE_URL}/api/consent/accept?version=2.0",
            headers=self.headers
        )
        assert accept_resp.status_code == 200
        assert accept_resp.json()["success"] == True
        
        # Step 4: Check status (should be true)
        status_resp_2 = requests.get(
            f"{BASE_URL}/api/consent/status",
            headers=self.headers
        )
        assert status_resp_2.status_code == 200
        assert status_resp_2.json()["accepted"] == True
        assert status_resp_2.json()["version"] == "2.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
