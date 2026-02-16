"""
Test Iteration 12: Privacy & Consent Features
- Profile reading history with translations
- Privacy page /privacy route
- Consent API: GET /api/consent/status, POST /api/consent/accept
- Badge 'Accettato' after term acceptance
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://settings-bugs-fix.preview.emergentagent.com')

class TestConsentAPI:
    """Test consent endpoints for GDPR compliance"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "testbible@cibospirituale.it", "password": "Test123!"},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            token = response.json().get("session_token")
            return token
        pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_consent_status_unauthorized(self):
        """Test consent status without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/consent/status")
        assert response.status_code == 401
        print("PASS: Consent status requires authentication")
    
    def test_consent_status_authenticated(self, auth_token):
        """Test consent status with auth returns valid response"""
        response = requests.get(
            f"{BASE_URL}/api/consent/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Should have 'accepted' field (boolean)
        assert "accepted" in data
        assert isinstance(data["accepted"], bool)
        print(f"PASS: Consent status returned: accepted={data['accepted']}")
        if data["accepted"]:
            assert "version" in data
            assert "accepted_at" in data
            print(f"  Version: {data.get('version')}, Accepted at: {data.get('accepted_at')}")
    
    def test_consent_accept_unauthorized(self):
        """Test consent accept without auth returns 401"""
        response = requests.post(
            f"{BASE_URL}/api/consent/accept?version=1.0.0"
        )
        assert response.status_code == 401
        print("PASS: Consent accept requires authentication")
    
    def test_consent_accept_missing_version(self, auth_token):
        """Test consent accept without version parameter fails"""
        response = requests.post(
            f"{BASE_URL}/api/consent/accept",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Should return 422 (Unprocessable Entity) for missing required param
        assert response.status_code == 422
        print("PASS: Consent accept requires version parameter")
    
    def test_consent_accept_success(self, auth_token):
        """Test consent accept with valid data succeeds"""
        response = requests.post(
            f"{BASE_URL}/api/consent/accept?version=1.0.0",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert data.get("version") == "1.0.0"
        assert "document_hash" in data
        assert "timestamp" in data
        print(f"PASS: Consent accepted - version: {data['version']}, hash: {data['document_hash'][:16]}...")
    
    def test_consent_status_after_accept(self, auth_token):
        """Verify consent status shows accepted after acceptance"""
        response = requests.get(
            f"{BASE_URL}/api/consent/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["accepted"] == True
        assert data.get("version") == "1.0.0"
        assert "accepted_at" in data
        print(f"PASS: Consent status shows accepted: True, version: {data['version']}")


class TestReadingHistoryAPI:
    """Test reading history endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "testbible@cibospirituale.it", "password": "Test123!"},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            token = response.json().get("session_token")
            return token
        pytest.skip("Authentication failed")
    
    def test_reading_history_get(self, auth_token):
        """Test get reading history returns list"""
        response = requests.get(
            f"{BASE_URL}/api/progress/reading/history?limit=20",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert isinstance(data["history"], list)
        print(f"PASS: Reading history returned {len(data['history'])} entries")
        
        # Verify structure of history items
        if data["history"]:
            entry = data["history"][0]
            assert "book" in entry
            assert "chapter" in entry
            assert "last_read" in entry
            print(f"  First entry: {entry['book']} {entry['chapter']}")
    
    def test_save_chapter_reading(self, auth_token):
        """Test saving a chapter reading creates history entry"""
        # Save a specific chapter reading
        response = requests.post(
            f"{BASE_URL}/api/progress/reading/chapter?book=Romani&chapter=8",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("book") == "Romani"
        assert data.get("chapter") == 8
        print(f"PASS: Saved chapter reading: Romani 8, read_count: {data.get('read_count')}")
    
    def test_reading_history_contains_saved_chapter(self, auth_token):
        """Verify saved chapter appears in reading history"""
        response = requests.get(
            f"{BASE_URL}/api/progress/reading/history?limit=20",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check if Romani 8 is in history
        romani_entries = [e for e in data["history"] if e["book"] == "Romani" and e["chapter"] == 8]
        assert len(romani_entries) > 0
        print(f"PASS: Romani 8 found in history with read_count: {romani_entries[0].get('read_count')}")


class TestProgressAPI:
    """Test progress endpoint for profile stats"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "testbible@cibospirituale.it", "password": "Test123!"},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            token = response.json().get("session_token")
            return token
        pytest.skip("Authentication failed")
    
    def test_get_progress(self, auth_token):
        """Test get progress returns user stats"""
        response = requests.get(
            f"{BASE_URL}/api/progress",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify progress structure
        assert "reading_streak" in data
        assert "total_chapters_read" in data
        assert "total_journal_entries" in data
        
        print(f"PASS: Progress - streak: {data['reading_streak']}, chapters: {data['total_chapters_read']}, entries: {data['total_journal_entries']}")


class TestMultiLanguageSupport:
    """Test that languages endpoint returns all 6 supported languages"""
    
    def test_get_languages(self):
        """Test languages endpoint returns 6 languages"""
        response = requests.get(f"{BASE_URL}/api/languages")
        assert response.status_code == 200
        data = response.json()
        
        expected_languages = ["it", "en", "es", "de", "fr", "pt"]
        for lang in expected_languages:
            assert lang in data
            assert "name" in data[lang]
            assert "flag" in data[lang]
            assert "tts_code" in data[lang]
            print(f"  {lang}: {data[lang]['name']} {data[lang]['flag']}")
        
        print(f"PASS: All 6 languages supported")
    
    def test_bible_books_italian(self):
        """Test Bible books in Italian"""
        response = requests.get(f"{BASE_URL}/api/bible/books?lang=it")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 30  # Should have many books
        assert data[0]["name"] == "Genesi"
        print(f"PASS: Italian Bible has {len(data)} books, first: {data[0]['name']}")
    
    def test_bible_books_english(self):
        """Test Bible books in English"""
        response = requests.get(f"{BASE_URL}/api/bible/books?lang=en")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 30
        assert data[0]["name"] == "Genesis"
        print(f"PASS: English Bible has {len(data)} books, first: {data[0]['name']}")
    
    def test_bible_books_spanish(self):
        """Test Bible books in Spanish"""
        response = requests.get(f"{BASE_URL}/api/bible/books?lang=es")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 30
        assert data[0]["name"] == "Génesis"
        print(f"PASS: Spanish Bible has {len(data)} books, first: {data[0]['name']}")


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "testbible@cibospirituale.it", "password": "Test123!"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "session_token" in data
        assert data["user"]["email"] == "testbible@cibospirituale.it"
        print(f"PASS: Login successful for {data['user']['email']}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 401"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "wrong@example.com", "password": "wrongpass"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 401
        print("PASS: Invalid credentials return 401")
    
    def test_auth_me(self):
        """Test /auth/me returns user data"""
        # First login
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "testbible@cibospirituale.it", "password": "Test123!"},
            headers={"Content-Type": "application/json"}
        )
        token = login_response.json().get("session_token")
        
        # Test /auth/me
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testbible@cibospirituale.it"
        print(f"PASS: /auth/me returns user: {data['name']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
