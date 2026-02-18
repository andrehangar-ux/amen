"""
Test Auth Endpoints - Registration, Login, Logout, Delete Account
Focus: User registration fix and auth flow verification
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://verse-mood-check.preview.emergentagent.com').rstrip('/')

class TestUserRegistration:
    """Test user registration endpoint - main bug fix verification"""
    
    def test_register_new_user_success(self):
        """Test that new user registration works correctly"""
        unique_email = f"test_reg_{uuid.uuid4().hex[:8]}@test.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "TestPass123!",
            "name": "Test Registration User",
            "language": "it"
        })
        
        print(f"Registration response status: {response.status_code}")
        print(f"Registration response: {response.text[:500]}")
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "user" in data, "Response should contain 'user' field"
        assert "session_token" in data, "Response should contain 'session_token' field"
        
        user = data["user"]
        assert user["email"] == unique_email, f"Email mismatch: {user['email']} != {unique_email}"
        assert user["name"] == "Test Registration User", f"Name mismatch: {user['name']}"
        assert "user_id" in user, "User should have user_id"
        
        # Verify session token is valid string
        assert isinstance(data["session_token"], str), "session_token should be string"
        assert len(data["session_token"]) > 10, "session_token should be non-empty"
        
        print(f"✓ Registration successful for {unique_email}")
        return data["session_token"], user["user_id"]
    
    def test_register_duplicate_email_fails(self):
        """Test that registering with existing email fails"""
        unique_email = f"test_dup_{uuid.uuid4().hex[:8]}@test.com"
        
        # First registration
        response1 = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "TestPass123!",
            "name": "First User"
        })
        assert response1.status_code == 200, f"First registration failed: {response1.text}"
        
        # Second registration with same email
        response2 = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "DifferentPass456!",
            "name": "Second User"
        })
        
        print(f"Duplicate registration response: {response2.status_code}")
        assert response2.status_code == 400, f"Expected 400 for duplicate email, got {response2.status_code}"
        
        data = response2.json()
        assert "detail" in data, "Error response should have 'detail' field"
        print(f"✓ Duplicate email correctly rejected: {data['detail']}")
    
    def test_register_missing_fields_fails(self):
        """Test that registration with missing fields fails"""
        # Missing password
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": "test@test.com",
            "name": "Test User"
        })
        
        assert response.status_code == 422, f"Expected 422 for missing password, got {response.status_code}"
        print("✓ Missing password correctly rejected")
        
        # Missing email
        response2 = requests.post(f"{BASE_URL}/api/auth/register", json={
            "password": "TestPass123!",
            "name": "Test User"
        })
        
        assert response2.status_code == 422, f"Expected 422 for missing email, got {response2.status_code}"
        print("✓ Missing email correctly rejected")


class TestLogin:
    """Test login endpoint"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        # First create a user
        unique_email = f"test_login_{uuid.uuid4().hex[:8]}@test.com"
        password = "TestPass123!"
        
        reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": password,
            "name": "Login Test User"
        })
        assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"
        
        # Now login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": unique_email,
            "password": password
        })
        
        print(f"Login response status: {login_response.status_code}")
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        data = login_response.json()
        assert "user" in data, "Login response should contain 'user'"
        assert "session_token" in data, "Login response should contain 'session_token'"
        assert data["user"]["email"] == unique_email
        
        print(f"✓ Login successful for {unique_email}")
        return data["session_token"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "WrongPassword123!"
        })
        
        print(f"Invalid login response: {response.status_code}")
        assert response.status_code == 401, f"Expected 401 for invalid credentials, got {response.status_code}"
        print("✓ Invalid credentials correctly rejected")


class TestLogout:
    """Test logout endpoint"""
    
    def test_logout_success(self):
        """Test logout functionality"""
        # Create and login user
        unique_email = f"test_logout_{uuid.uuid4().hex[:8]}@test.com"
        
        reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "TestPass123!",
            "name": "Logout Test User"
        })
        assert reg_response.status_code == 200
        session_token = reg_response.json()["session_token"]
        
        # Logout
        logout_response = requests.post(
            f"{BASE_URL}/api/auth/logout",
            headers={"Authorization": f"Bearer {session_token}"}
        )
        
        print(f"Logout response: {logout_response.status_code}")
        assert logout_response.status_code == 200, f"Logout failed: {logout_response.text}"
        
        data = logout_response.json()
        assert "message" in data
        print(f"✓ Logout successful: {data['message']}")


class TestDeleteAccount:
    """Test delete account endpoint"""
    
    def test_delete_account_success(self):
        """Test account deletion"""
        # Create user
        unique_email = f"test_delete_{uuid.uuid4().hex[:8]}@test.com"
        
        reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "TestPass123!",
            "name": "Delete Test User"
        })
        assert reg_response.status_code == 200
        session_token = reg_response.json()["session_token"]
        
        # Delete account
        delete_response = requests.delete(
            f"{BASE_URL}/api/auth/delete-account",
            headers={"Authorization": f"Bearer {session_token}"}
        )
        
        print(f"Delete account response: {delete_response.status_code}")
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        
        data = delete_response.json()
        assert "message" in data
        print(f"✓ Account deletion successful: {data['message']}")
        
        # Verify user can't login anymore
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": unique_email,
            "password": "TestPass123!"
        })
        assert login_response.status_code == 401, "Deleted user should not be able to login"
        print("✓ Deleted user correctly cannot login")
    
    def test_delete_account_requires_auth(self):
        """Test that delete account requires authentication"""
        response = requests.delete(f"{BASE_URL}/api/auth/delete-account")
        
        print(f"Unauthenticated delete response: {response.status_code}")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("✓ Delete account correctly requires authentication")


class TestAuthWithTestCredentials:
    """Test with provided test credentials"""
    
    def test_login_with_test_credentials(self):
        """Test login with provided test credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testbible@cibospirituale.it",
            "password": "Test123!"
        })
        
        print(f"Test credentials login response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            assert "user" in data
            assert "session_token" in data
            print(f"✓ Test credentials login successful")
            return data["session_token"]
        else:
            print(f"Note: Test credentials may not exist yet: {response.text}")
            pytest.skip("Test credentials not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
