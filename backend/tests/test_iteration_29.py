"""
Iteration 29 - Testing:
1. Backend mood-checkin API - verifying verses change on consecutive calls
2. Frontend 'Salvati' button in Bible toolbar
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://spirit-study-update.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "testbible@cibospirituale.it"
TEST_PASSWORD = "Test123!"

class TestMoodCheckinAPI:
    """Tests for /api/ai/mood-checkin endpoint - verifying verse randomization"""
    
    @pytest.fixture(scope="class")
    def session(self):
        """Create authenticated session"""
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        return s
    
    @pytest.fixture(scope="class")
    def auth_token(self, session):
        """Login and get session token"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        token = data.get("session_token")
        assert token, "No session token in response"
        return token
    
    @pytest.fixture(scope="class")
    def auth_session(self, session, auth_token):
        """Session with auth header"""
        session.headers.update({"Authorization": f"Bearer {auth_token}"})
        return session
    
    def test_mood_checkin_returns_verse(self, auth_session):
        """Test that mood-checkin API returns a verse"""
        response = auth_session.post(f"{BASE_URL}/api/ai/mood-checkin", json={
            "mood": "felice",
            "language": "it"
        })
        assert response.status_code == 200, f"Mood checkin failed: {response.text}"
        
        data = response.json()
        assert "verse" in data, "Response should contain 'verse'"
        assert "ref" in data["verse"], "Verse should have 'ref'"
        assert "text" in data["verse"], "Verse should have 'text'"
        assert "reflection" in data, "Response should contain 'reflection'"
        print(f"First call verse: {data['verse']['ref']}")
    
    def test_mood_checkin_consecutive_calls_different_verses(self, auth_session):
        """Test that 5 consecutive calls for same mood return different verses"""
        mood = "triste"  # Has multiple verses
        verses_received = []
        
        for i in range(5):
            response = auth_session.post(f"{BASE_URL}/api/ai/mood-checkin", json={
                "mood": mood,
                "language": "it"
            })
            assert response.status_code == 200, f"Call {i+1} failed: {response.text}"
            
            data = response.json()
            verse_ref = data["verse"]["ref"]
            verses_received.append(verse_ref)
            print(f"Call {i+1}: {verse_ref}")
        
        # Check that we got at least 2 different verses in 5 calls
        unique_verses = set(verses_received)
        print(f"Unique verses in 5 calls: {len(unique_verses)} - {unique_verses}")
        
        # With random.choice and multiple verses available, probability of all same is very low
        # We expect at least 2 unique verses (allowing some randomness)
        assert len(unique_verses) >= 2, f"Expected at least 2 different verses but got only: {unique_verses}"
    
    def test_mood_checkin_anxious_mood(self, auth_session):
        """Test anxious mood verses change"""
        mood = "ansioso"
        verses_received = []
        
        for i in range(5):
            response = auth_session.post(f"{BASE_URL}/api/ai/mood-checkin", json={
                "mood": mood,
                "language": "it"
            })
            assert response.status_code == 200, f"Call {i+1} failed: {response.text}"
            
            data = response.json()
            verse_ref = data["verse"]["ref"]
            verses_received.append(verse_ref)
            print(f"Anxious mood call {i+1}: {verse_ref}")
        
        unique_verses = set(verses_received)
        print(f"Unique anxious verses in 5 calls: {len(unique_verses)}")
        assert len(unique_verses) >= 2, f"Expected different verses for anxious mood"
    
    def test_mood_checkin_english_language(self, auth_session):
        """Test mood checkin in English"""
        response = auth_session.post(f"{BASE_URL}/api/ai/mood-checkin", json={
            "mood": "happy",
            "language": "en"
        })
        assert response.status_code == 200, f"English mood checkin failed: {response.text}"
        
        data = response.json()
        assert data["language"] == "en", "Language should be 'en'"
        print(f"English verse: {data['verse']['ref']} - {data['verse']['text'][:50]}...")
    
    def test_mood_checkin_spanish_language(self, auth_session):
        """Test mood checkin in Spanish"""
        response = auth_session.post(f"{BASE_URL}/api/ai/mood-checkin", json={
            "mood": "triste",
            "language": "es"
        })
        assert response.status_code == 200, f"Spanish mood checkin failed: {response.text}"
        
        data = response.json()
        assert data["language"] == "es", "Language should be 'es'"
        print(f"Spanish verse: {data['verse']['ref']} - {data['verse']['text'][:50]}...")


class TestMyContentEndpoint:
    """Tests for /my-content related endpoints (bookmarks, notes, highlights)"""
    
    @pytest.fixture(scope="class")
    def session(self):
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        return s
    
    @pytest.fixture(scope="class")
    def auth_token(self, session):
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json().get("session_token")
    
    @pytest.fixture(scope="class")
    def auth_session(self, session, auth_token):
        session.headers.update({"Authorization": f"Bearer {auth_token}"})
        return session
    
    def test_get_user_bookmarks(self, auth_session):
        """Test fetching user bookmarks"""
        response = auth_session.get(f"{BASE_URL}/api/bookmarks")
        assert response.status_code == 200, f"Get bookmarks failed: {response.text}"
        
        data = response.json()
        # Could be empty list or list of bookmarks
        assert isinstance(data, list), "Bookmarks should be a list"
        print(f"User has {len(data)} bookmarks")
    
    def test_create_bookmark(self, auth_session):
        """Test creating a bookmark"""
        # Create a test bookmark
        bookmark_data = {
            "book": "Salmi",
            "chapter": 23,
            "verse": 1,
            "text": "L'Eterno è il mio pastore, nulla mi mancherà.",
            "note": "Test bookmark from iteration 29",
            "highlight_color": "#FFD700"
        }
        
        response = auth_session.post(f"{BASE_URL}/api/bookmarks", json=bookmark_data)
        assert response.status_code in [200, 201], f"Create bookmark failed: {response.text}"
        
        data = response.json()
        assert "bookmark_id" in data, "Response should contain bookmark_id"
        print(f"Created bookmark: {data['bookmark_id']}")
        
        # Store for cleanup
        self.__class__.test_bookmark_id = data["bookmark_id"]
    
    def test_get_study_data_includes_bookmarks(self, auth_session):
        """Test that study data endpoint returns user_bookmarks"""
        response = auth_session.get(f"{BASE_URL}/api/bible/study/Salmi/23")
        assert response.status_code == 200, f"Get study data failed: {response.text}"
        
        data = response.json()
        # Should have user_bookmarks key (even if empty)
        assert "user_bookmarks" in data or "user_notes" in data, "Study data should include user data"
        print(f"Study data keys: {list(data.keys())}")
    
    def test_delete_bookmark_cleanup(self, auth_session):
        """Cleanup: delete test bookmark"""
        bookmark_id = getattr(self.__class__, 'test_bookmark_id', None)
        if bookmark_id:
            response = auth_session.delete(f"{BASE_URL}/api/bookmarks/{bookmark_id}")
            # Accept 200 or 404 (if already deleted)
            assert response.status_code in [200, 404], f"Delete bookmark failed: {response.text}"
            print(f"Deleted test bookmark: {bookmark_id}")


class TestBibleToolbarEndpoints:
    """Test endpoints used by Bible toolbar"""
    
    @pytest.fixture(scope="class")
    def session(self):
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        return s
    
    @pytest.fixture(scope="class") 
    def auth_token(self, session):
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json().get("session_token")
    
    @pytest.fixture(scope="class")
    def auth_session(self, session, auth_token):
        session.headers.update({"Authorization": f"Bearer {auth_token}"})
        return session
    
    def test_bible_editions_endpoint(self, auth_session):
        """Test Bible editions endpoint"""
        response = auth_session.get(f"{BASE_URL}/api/bible/editions")
        assert response.status_code == 200, f"Get editions failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, dict), "Editions should be a dict"
        assert len(data) > 0, "Should have at least one edition"
        print(f"Available editions: {list(data.keys())}")
    
    def test_bible_books_endpoint(self, auth_session):
        """Test Bible books endpoint"""
        response = auth_session.get(f"{BASE_URL}/api/bible/books?lang=it")
        assert response.status_code == 200, f"Get books failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Books should be a list"
        assert len(data) > 0, "Should have books"
        print(f"Found {len(data)} books in Italian")
    
    def test_languages_endpoint(self, auth_session):
        """Test languages endpoint"""
        response = auth_session.get(f"{BASE_URL}/api/languages")
        assert response.status_code == 200, f"Get languages failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, dict), "Languages should be a dict"
        assert "it" in data, "Should have Italian"
        assert "en" in data, "Should have English"
        print(f"Supported languages: {list(data.keys())}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
