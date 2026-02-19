"""
Iteration 13 Test: T&C checkbox, Delete Account, Logout, Auto-login features
Test features:
1. DELETE /api/auth/delete-account - Delete user account
2. POST /api/auth/logout - Logout endpoint
3. Login/Register flow with session token
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://spirit-study-update.preview.emergentagent.com').rstrip('/')

class TestAuthEndpoints:
    """Test auth endpoints for delete account and logout"""
    
    def test_health_check(self):
        """Test health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✓ Health check passed")

    def test_login_with_valid_credentials(self):
        """Test login with valid test credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testbible@cibospirituale.it",
            "password": "Test123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "session_token" in data
        assert "user" in data
        assert data["user"]["email"] == "testbible@cibospirituale.it"
        print(f"✓ Login successful, token: {data['session_token'][:20]}...")
        return data["session_token"]

    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid login correctly rejected with 401")

    def test_get_me_without_auth(self):
        """Test /auth/me without authentication"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print("✓ /auth/me without auth returns 401")

    def test_get_me_with_auth(self):
        """Test /auth/me with valid token"""
        # First login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testbible@cibospirituale.it",
            "password": "Test123!"
        })
        token = login_response.json()["session_token"]
        
        # Then get me
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testbible@cibospirituale.it"
        print(f"✓ /auth/me returns user: {data['name']}")

    def test_logout_endpoint(self):
        """Test logout endpoint"""
        # First login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testbible@cibospirituale.it",
            "password": "Test123!"
        })
        token = login_response.json()["session_token"]
        
        # Then logout
        response = requests.post(f"{BASE_URL}/api/auth/logout", headers={
            "Authorization": f"Bearer {token}"
        }, cookies={"session_token": token})
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ Logout successful: {data['message']}")

    def test_logout_without_auth(self):
        """Test logout without authentication (should still return 200)"""
        response = requests.post(f"{BASE_URL}/api/auth/logout")
        assert response.status_code == 200
        print("✓ Logout without auth returns 200")

    def test_delete_account_without_auth(self):
        """Test delete account without authentication"""
        response = requests.delete(f"{BASE_URL}/api/auth/delete-account")
        assert response.status_code == 401
        print("✓ Delete account without auth returns 401")

    def test_register_and_delete_account_flow(self):
        """Test full register and delete account flow"""
        # Create unique test user
        test_email = f"TEST_delete_{uuid.uuid4().hex[:8]}@test.com"
        test_password = "TestDelete123!"
        test_name = "Test Delete User"
        
        # Register
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": test_password,
            "name": test_name
        })
        assert register_response.status_code == 200
        data = register_response.json()
        assert "session_token" in data
        token = data["session_token"]
        print(f"✓ Registered test user: {test_email}")
        
        # Verify user exists with /auth/me
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert me_response.status_code == 200
        print("✓ User verified via /auth/me")
        
        # Delete account
        delete_response = requests.delete(f"{BASE_URL}/api/auth/delete-account", headers={
            "Authorization": f"Bearer {token}"
        })
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert "message" in data
        print(f"✓ Account deleted: {data['message']}")
        
        # Verify user no longer exists (login should fail)
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": test_email,
            "password": test_password
        })
        assert login_response.status_code == 401
        print("✓ Login fails after account deletion (verified account removed)")

    def test_session_token_persistence(self):
        """Test that session token allows persistent login"""
        # Login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testbible@cibospirituale.it",
            "password": "Test123!"
        })
        token = login_response.json()["session_token"]
        
        # Make multiple requests with same token
        for i in range(3):
            response = requests.get(f"{BASE_URL}/api/auth/me", headers={
                "Authorization": f"Bearer {token}"
            })
            assert response.status_code == 200
        
        print("✓ Session token works for multiple requests (auto-login supported)")


class TestRegisterValidation:
    """Test register endpoint validation"""
    
    def test_register_duplicate_email(self):
        """Test registering with existing email fails"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": "testbible@cibospirituale.it",
            "password": "Test123!",
            "name": "Duplicate User"
        })
        assert response.status_code == 400
        data = response.json()
        assert "già registrata" in data.get("detail", "").lower() or "email" in data.get("detail", "").lower()
        print("✓ Duplicate email registration rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
