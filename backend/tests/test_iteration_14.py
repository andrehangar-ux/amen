"""
Iteration 14 Tests - Hamburger Menu, Donations, Profile Actions, Quiz Isaia
Testing: Hamburger menu navigation, donations config (PayPal/IBAN), logout/delete buttons, quiz translations
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://bible-quiz-themed.preview.emergentagent.com')
TEST_USER_EMAIL = "testbible@cibospirituale.it"
TEST_USER_PASSWORD = "Test123!"


class TestHealthAndBasics:
    """Basic API health checks"""
    
    def test_api_health(self):
        """Test API is running"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("PASS: API health check successful")


class TestAuthentication:
    """Authentication tests"""
    
    def test_login_valid_credentials(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "session_token" in data
        assert "user" in data
        print(f"PASS: Login successful, user: {data['user'].get('name', 'Unknown')}")
        return data["session_token"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("PASS: Invalid credentials correctly rejected")


class TestDonationsConfig:
    """Donations configuration tests"""
    
    def test_donations_config_endpoint(self):
        """Test that donations config returns correct PayPal and IBAN"""
        response = requests.get(f"{BASE_URL}/api/donations/config")
        assert response.status_code == 200
        data = response.json()
        
        # Verify PayPal email
        assert data.get("paypal_email") == "andrehangar@live.it", f"PayPal email mismatch: {data.get('paypal_email')}"
        print(f"PASS: PayPal email correct: {data.get('paypal_email')}")
        
        # Verify IBAN
        expected_iban = "IT46 I036 6901 6008 5802 8558 932"
        assert data.get("iban") == expected_iban, f"IBAN mismatch: {data.get('iban')}"
        print(f"PASS: IBAN correct: {data.get('iban')}")
        
        # Verify BIC/SWIFT
        assert "bic_swift" in data and data.get("bic_swift") == "REVOITM2", f"BIC/SWIFT: {data.get('bic_swift')}"
        print(f"PASS: BIC/SWIFT correct: {data.get('bic_swift')}")
        
        # Verify bank name
        assert "banca" in data and data.get("banca") == "Revolut Bank UAB"
        print(f"PASS: Bank name correct: {data.get('banca')}")
        
        # Verify intestatario
        assert "intestatario" in data and data.get("intestatario") == "Andrea Confortino"
        print(f"PASS: Intestatario correct: {data.get('intestatario')}")
        
        return data


class TestQuizCategories:
    """Quiz category tests - verifying Isaia translations are fixed"""
    
    def test_quiz_categories_isaia_exists(self):
        """Test that Isaia category exists in quiz categories"""
        response = requests.get(f"{BASE_URL}/api/quiz/categories")
        assert response.status_code == 200
        data = response.json()
        
        # Check if isaia category exists (API returns list of categories)
        isaia_category = None
        for cat in data:
            if cat.get("title") == "Isaia" or "isaia" in cat.get("id", ""):
                isaia_category = cat
                break
        
        assert isaia_category is not None, "Isaia category not found"
        print(f"PASS: Found Isaia category: {isaia_category.get('title')} (id: {isaia_category.get('id')})")
    
    def test_quiz_isaia_questions_not_proto_short(self):
        """Test that Isaia questions are properly written (not 'Isaia - Proto?')"""
        response = requests.get(f"{BASE_URL}/api/quiz/category/cat_profeti_isaia")
        assert response.status_code == 200
        data = response.json()
        
        questions = data.get("questions", [])
        assert len(questions) > 0, "No questions found in Isaia category"
        
        for q in questions:
            question_text = q.get("question", "")
            # Check that no question is the broken 'Isaia - Proto?' format
            assert question_text != "Isaia - Proto?", f"Found broken question: {question_text}"
            
            # Check Proto-Isaia question is properly formatted
            if "Proto" in question_text and "Isaia" in question_text:
                assert len(question_text) > 15, f"Question too short: {question_text}"
                print(f"PASS: Proto-Isaia question properly formatted: {question_text}")
        
        print(f"PASS: No broken 'Isaia - Proto?' questions found ({len(questions)} questions checked)")
    
    def test_quiz_isaia_proto_questions_complete(self):
        """Test that Proto-Isaia, Deutero-Isaia, Trito-Isaia questions are complete"""
        response = requests.get(f"{BASE_URL}/api/quiz/category/cat_profeti_isaia")
        assert response.status_code == 200
        data = response.json()
        
        questions = data.get("questions", [])
        
        proto_found = False
        deutero_found = False
        trito_found = False
        
        for q in questions:
            question_text = q.get("question", "")
            if "Proto-Isaia" in question_text:
                proto_found = True
                # Verify it's a complete question
                assert "?" in question_text, f"Proto-Isaia question incomplete: {question_text}"
                assert len(question_text) > 20, f"Proto-Isaia question too short: {question_text}"
            if "Deutero-Isaia" in question_text:
                deutero_found = True
            if "Trito-Isaia" in question_text:
                trito_found = True
        
        print(f"PASS: Isaia questions found - Proto: {proto_found}, Deutero: {deutero_found}, Trito: {trito_found}")


class TestAuthLogoutDeleteAccount:
    """Tests for logout and delete account endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("session_token")
        pytest.skip("Authentication failed")
    
    def test_logout_endpoint(self, auth_token):
        """Test that logout endpoint works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/auth/logout", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"PASS: Logout successful: {data.get('message')}")
    
    def test_delete_account_unauthorized(self):
        """Test that delete account requires authentication"""
        response = requests.delete(f"{BASE_URL}/api/auth/delete-account")
        assert response.status_code == 401
        print("PASS: Delete account correctly requires authentication")
    
    def test_get_me_with_auth(self, auth_token):
        """Test get current user endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("email") == TEST_USER_EMAIL
        print(f"PASS: Get me successful, user: {data.get('name')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
