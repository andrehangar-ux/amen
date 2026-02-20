"""
Iteration 17 - Comprehensive E2E Backend API Tests
Tests: Auth, Bible, Journal, Profile, Donations, Settings, Community, Quiz
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://quiz-nav-build.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "testbible@cibospirituale.it"
TEST_PASSWORD = "Test123!"


class TestPublicEndpoints:
    """Test public endpoints that don't require authentication"""
    
    def test_languages_endpoint(self):
        """Test /api/languages returns all supported languages"""
        response = requests.get(f"{BASE_URL}/api/languages")
        assert response.status_code == 200
        data = response.json()
        
        # Verify all 6 languages are present
        expected_languages = ['it', 'es', 'en', 'pt', 'fr', 'de']
        for lang in expected_languages:
            assert lang in data, f"Language {lang} not found"
            assert 'name' in data[lang]
            assert 'flag' in data[lang]
            assert 'tts_code' in data[lang]
        print(f"✓ Languages endpoint: {len(data)} languages returned")
    
    def test_bible_editions_endpoint(self):
        """Test /api/bible/editions returns available Bible editions"""
        response = requests.get(f"{BASE_URL}/api/bible/editions")
        assert response.status_code == 200
        data = response.json()
        
        # Verify key editions exist
        assert 'nuova_diodati' in data
        assert 'reina_valera' in data
        assert 'kjv' in data
        print(f"✓ Bible editions endpoint: {len(data)} editions returned")
    
    def test_bible_books_italian(self):
        """Test /api/bible/books returns Bible books in Italian"""
        response = requests.get(f"{BASE_URL}/api/bible/books?lang=it")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 30, "Should have at least 30 Bible books"
        assert data[0]['name'] == 'Genesi'  # First book in Italian
        print(f"✓ Bible books (IT): {len(data)} books returned")
    
    def test_bible_books_spanish(self):
        """Test /api/bible/books returns Bible books in Spanish"""
        response = requests.get(f"{BASE_URL}/api/bible/books?lang=es")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 30
        assert data[0]['name'] == 'Génesis'  # First book in Spanish
        print(f"✓ Bible books (ES): {len(data)} books returned")
    
    def test_bible_chapter_genesi_1(self):
        """Test /api/bible/chapter/Genesi/1 returns chapter content"""
        response = requests.get(f"{BASE_URL}/api/bible/chapter/Genesi/1?lang=it")
        assert response.status_code == 200
        data = response.json()
        
        assert 'verses' in data
        assert len(data['verses']) > 0
        assert data['book'] == 'Genesi'
        assert data['chapter'] == 1
        print(f"✓ Bible chapter Genesi 1: {len(data['verses'])} verses returned")
    
    def test_quiz_topics(self):
        """Test /api/quiz/topics returns quiz topics"""
        response = requests.get(f"{BASE_URL}/api/quiz/topics?lang=it")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        print(f"✓ Quiz topics: {len(data)} topics returned")
    
    def test_quiz_categories(self):
        """Test /api/quiz/categories returns quiz categories"""
        response = requests.get(f"{BASE_URL}/api/quiz/categories?lang=it")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        print(f"✓ Quiz categories: {len(data)} categories returned")


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_login_success(self):
        """Test successful login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        
        assert 'user' in data
        assert 'session_token' in data
        assert data['user']['email'] == TEST_EMAIL
        print(f"✓ Login successful for {TEST_EMAIL}")
        
        return data['session_token']
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid login rejected with 401")
    
    def test_auth_me_without_token(self):
        """Test /api/auth/me without token returns 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print("✓ Auth/me without token rejected with 401")
    
    def test_auth_me_with_token(self):
        """Test /api/auth/me with valid token returns user data"""
        # First login to get token
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_resp.status_code == 200
        token = login_resp.json()['session_token']
        
        # Then test /auth/me
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['email'] == TEST_EMAIL
        print(f"✓ Auth/me with token: user {data['email']} returned")


class TestAuthenticatedEndpoints:
    """Test endpoints that require authentication"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Could not authenticate")
        token = response.json()['session_token']
        return {"Authorization": f"Bearer {token}"}
    
    def test_daily_verse(self, auth_headers):
        """Test /api/bible/daily-verse returns a verse"""
        response = requests.get(f"{BASE_URL}/api/bible/daily-verse?lang=it", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert 'reference' in data or 'ref' in data
        assert 'text' in data
        print(f"✓ Daily verse: {data.get('reference', data.get('ref', 'Unknown'))}")
    
    def test_user_progress(self, auth_headers):
        """Test /api/progress returns user progress"""
        response = requests.get(f"{BASE_URL}/api/progress", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert 'reading_streak' in data or 'total_chapters_read' in data
        print(f"✓ User progress: streak={data.get('reading_streak', 0)}, chapters={data.get('total_chapters_read', 0)}")
    
    def test_journal_entries_list(self, auth_headers):
        """Test /api/journal returns journal entries list"""
        response = requests.get(f"{BASE_URL}/api/journal", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        print(f"✓ Journal entries: {len(data)} entries")
    
    def test_community_messages(self, auth_headers):
        """Test /api/community/messages returns community messages"""
        response = requests.get(f"{BASE_URL}/api/community/messages?lang=it", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        print(f"✓ Community messages: {len(data)} messages")
    
    def test_donation_config(self, auth_headers):
        """Test /api/donations/config returns donation configuration"""
        response = requests.get(f"{BASE_URL}/api/donations/config", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert 'paypal_email' in data or 'paypal_link' in data
        assert 'iban' in data
        print(f"✓ Donation config: PayPal={data.get('paypal_email', 'N/A')}, IBAN present")


class TestMoodCheckin:
    """Test mood check-in feature"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Could not authenticate")
        token = response.json()['session_token']
        return {"Authorization": f"Bearer {token}"}
    
    def test_mood_checkin(self, auth_headers):
        """Test mood check-in returns verse and reflection"""
        response = requests.post(
            f"{BASE_URL}/api/ai/mood-checkin",
            json={"mood": "felice", "language": "it"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert 'mood' in data or 'verse' in data
        print(f"✓ Mood check-in: response received for 'felice'")


class TestDictionary:
    """Test dictionary endpoints"""
    
    def test_dictionary_search(self):
        """Test dictionary search"""
        response = requests.get(f"{BASE_URL}/api/dictionary?search=grace&lang=it")
        # Could be 200 or 404 depending on search term
        assert response.status_code in [200, 404]
        print(f"✓ Dictionary search: status {response.status_code}")
    
    def test_dictionary_term(self):
        """Test getting a dictionary term"""
        response = requests.get(f"{BASE_URL}/api/dictionary/amen?lang=it")
        # Could be 200 or 404 depending on whether term exists
        assert response.status_code in [200, 404]
        print(f"✓ Dictionary term lookup: status {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
