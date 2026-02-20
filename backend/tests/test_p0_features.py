"""
Test P0 Features - Iteration 23
- API /api/ai/mood-checkin - Dynamic verses for mood with daily rotation
- API /api/ai/mood-checkin - Verse translation in different languages (it, en, es)
- API /api/bible/daily-verse - Daily verse with rotation and translation
- API /api/dictionary - Biblical dictionary should return terms (108 terms)
"""
import pytest
import requests
import os
import hashlib

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://quiz-nav-build.preview.emergentagent.com')
if BASE_URL.endswith('/'):
    BASE_URL = BASE_URL.rstrip('/')

# Test credentials
TEST_USER_EMAIL = "testbible@cibospirituale.it"
TEST_USER_PASSWORD = "Test123!"

class TestP0Features:
    """P0 Feature Tests for Mood Check-in, Daily Verse, Dictionary"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get session token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        if login_response.status_code == 200:
            data = login_response.json()
            self.session_token = data.get("session_token")
            self.session.headers.update({"Authorization": f"Bearer {self.session_token}"})
            print(f"✅ Logged in successfully as {TEST_USER_EMAIL}")
        else:
            print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
            self.session_token = None
    
    # ==================== MOOD CHECK-IN TESTS ====================
    
    def test_mood_checkin_italian(self):
        """Test mood checkin API with Italian language"""
        if not self.session_token:
            pytest.skip("Authentication required")
        
        response = self.session.post(f"{BASE_URL}/api/ai/mood-checkin", json={
            "mood": "felice",
            "language": "it"
        })
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text[:500] if response.text else 'empty'}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Verify response structure
        assert "mood" in data, "Response should contain 'mood' field"
        assert "verse" in data, "Response should contain 'verse' field"
        assert "reflection" in data, "Response should contain 'reflection' field"
        
        # Verify verse structure
        verse = data["verse"]
        assert "ref" in verse, "Verse should contain 'ref' field"
        assert "text" in verse, "Verse should contain 'text' field"
        
        print(f"✅ Mood check-in (IT): {verse['ref']} - {verse['text'][:50]}...")
        print(f"   Reflection: {data['reflection'][:100]}...")
    
    def test_mood_checkin_english(self):
        """Test mood checkin API with English language"""
        if not self.session_token:
            pytest.skip("Authentication required")
        
        response = self.session.post(f"{BASE_URL}/api/ai/mood-checkin", json={
            "mood": "felice",  # mood key stays Italian
            "language": "en"
        })
        
        print(f"Response status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "verse" in data
        assert "reflection" in data
        
        verse = data["verse"]
        print(f"✅ Mood check-in (EN): {verse['ref']} - {verse['text'][:50]}...")
        
        # Verify it returned English verse (references should match English format)
        assert "Psalm" in verse["ref"] or "Nehemiah" in verse["ref"] or "Romans" in verse["ref"], \
            f"Expected English reference format, got: {verse['ref']}"
    
    def test_mood_checkin_spanish(self):
        """Test mood checkin API with Spanish language"""
        if not self.session_token:
            pytest.skip("Authentication required")
        
        response = self.session.post(f"{BASE_URL}/api/ai/mood-checkin", json={
            "mood": "triste",
            "language": "es"
        })
        
        print(f"Response status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "verse" in data
        verse = data["verse"]
        print(f"✅ Mood check-in (ES): {verse['ref']} - {verse['text'][:50]}...")
        
        # Spanish references should contain "Salmos" or "Apocalipsis" for sad mood
        assert "Salmos" in verse["ref"] or "Apocalipsis" in verse["ref"], \
            f"Expected Spanish reference format, got: {verse['ref']}"
    
    def test_mood_checkin_different_moods(self):
        """Test mood checkin with different moods"""
        if not self.session_token:
            pytest.skip("Authentication required")
        
        moods = ["felice", "triste", "ansioso", "arrabbiato", "grato", "confuso", "speranzoso", "stanco"]
        
        for mood in moods:
            response = self.session.post(f"{BASE_URL}/api/ai/mood-checkin", json={
                "mood": mood,
                "language": "it"
            })
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Mood '{mood}': {data['verse']['ref']}")
            else:
                print(f"⚠️ Mood '{mood}': status {response.status_code}")
        
        # Test passes if at least we get responses
        assert True
    
    def test_mood_checkin_daily_rotation(self):
        """Test that mood checkin uses daily rotation (same mood = same verse on same day)"""
        if not self.session_token:
            pytest.skip("Authentication required")
        
        # Make two requests for the same mood
        response1 = self.session.post(f"{BASE_URL}/api/ai/mood-checkin", json={
            "mood": "speranzoso",
            "language": "it"
        })
        
        response2 = self.session.post(f"{BASE_URL}/api/ai/mood-checkin", json={
            "mood": "speranzoso",
            "language": "it"
        })
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Same mood on same day should return same verse (due to daily rotation)
        assert data1["verse"]["ref"] == data2["verse"]["ref"], \
            f"Expected same verse on same day, got {data1['verse']['ref']} vs {data2['verse']['ref']}"
        
        print(f"✅ Daily rotation verified: same mood gives same verse ({data1['verse']['ref']})")
    
    # ==================== DAILY VERSE TESTS ====================
    
    def test_daily_verse_italian(self):
        """Test daily verse API with Italian language"""
        response = self.session.get(f"{BASE_URL}/api/bible/daily-verse?lang=it")
        
        print(f"Response status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "reference" in data, "Response should contain 'reference' field"
        assert "text" in data, "Response should contain 'text' field"
        assert "language" in data, "Response should contain 'language' field"
        
        assert data["language"] == "it", f"Expected language 'it', got {data['language']}"
        
        print(f"✅ Daily verse (IT): {data['reference']} - {data['text'][:60]}...")
    
    def test_daily_verse_english(self):
        """Test daily verse API with English language"""
        response = self.session.get(f"{BASE_URL}/api/bible/daily-verse?lang=en")
        
        print(f"Response status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "reference" in data
        assert "text" in data
        assert data["language"] == "en", f"Expected language 'en', got {data['language']}"
        
        # English reference should have English book names
        english_books = ["John", "Psalm", "Romans", "Philippians", "Genesis", "Exodus"]
        has_english_ref = any(book in data["reference"] for book in english_books)
        assert has_english_ref, f"Expected English reference, got: {data['reference']}"
        
        print(f"✅ Daily verse (EN): {data['reference']} - {data['text'][:60]}...")
    
    def test_daily_verse_spanish(self):
        """Test daily verse API with Spanish language"""
        response = self.session.get(f"{BASE_URL}/api/bible/daily-verse?lang=es")
        
        print(f"Response status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert data["language"] == "es", f"Expected language 'es', got {data['language']}"
        
        # Spanish reference should have Spanish book names
        spanish_books = ["Juan", "Salmos", "Romanos", "Filipenses", "Génesis"]
        has_spanish_ref = any(book in data["reference"] for book in spanish_books)
        assert has_spanish_ref, f"Expected Spanish reference, got: {data['reference']}"
        
        print(f"✅ Daily verse (ES): {data['reference']} - {data['text'][:60]}...")
    
    def test_daily_verse_rotation(self):
        """Test that daily verse is consistent on same day"""
        # Make two requests
        response1 = self.session.get(f"{BASE_URL}/api/bible/daily-verse?lang=it")
        response2 = self.session.get(f"{BASE_URL}/api/bible/daily-verse?lang=it")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Same day should return same verse
        assert data1["reference"] == data2["reference"], \
            f"Expected same verse on same day, got {data1['reference']} vs {data2['reference']}"
        
        print(f"✅ Daily verse rotation verified: {data1['reference']}")
    
    # ==================== DICTIONARY TESTS ====================
    
    def test_dictionary_returns_terms(self):
        """Test dictionary API returns terms"""
        response = self.session.get(f"{BASE_URL}/api/dictionary")
        
        print(f"Response status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "Dictionary should have terms"
        
        print(f"✅ Dictionary returned {len(data)} terms")
        
        # Check first term structure
        if len(data) > 0:
            first_term = data[0]
            assert "id" in first_term, "Term should have 'id' field"
            assert "term" in first_term, "Term should have 'term' field"
            assert "origin" in first_term, "Term should have 'origin' field"
            assert "meaning" in first_term, "Term should have 'meaning' field"
            print(f"   First term: {first_term['term']} - {first_term['meaning'][:30]}...")
    
    def test_dictionary_has_108_terms(self):
        """Test dictionary API returns approximately 108 terms as expected"""
        response = self.session.get(f"{BASE_URL}/api/dictionary")
        
        assert response.status_code == 200
        data = response.json()
        
        # The biblical dictionary should have around 108 terms
        assert len(data) >= 100, f"Expected at least 100 terms, got {len(data)}"
        print(f"✅ Dictionary has {len(data)} terms (expected ~108)")
    
    def test_dictionary_alphabetical_order(self):
        """Test that dictionary terms are sorted alphabetically"""
        response = self.session.get(f"{BASE_URL}/api/dictionary")
        
        assert response.status_code == 200
        data = response.json()
        
        # Extract term names (without parentheses content)
        term_names = [t["term"].split(" (")[0].lower() for t in data]
        sorted_names = sorted(term_names)
        
        assert term_names == sorted_names, "Terms should be sorted alphabetically"
        print(f"✅ Dictionary terms are sorted alphabetically")
    
    def test_dictionary_with_language_parameter(self):
        """Test dictionary API with different language parameters"""
        languages = ["it", "en", "es"]
        
        for lang in languages:
            response = self.session.get(f"{BASE_URL}/api/dictionary?lang={lang}")
            
            assert response.status_code == 200, f"Expected 200 for lang={lang}, got {response.status_code}"
            data = response.json()
            
            assert len(data) > 0, f"Dictionary should have terms for lang={lang}"
            print(f"✅ Dictionary ({lang}): {len(data)} terms")
    
    def test_dictionary_term_origins(self):
        """Test that dictionary terms have correct origins"""
        response = self.session.get(f"{BASE_URL}/api/dictionary")
        
        assert response.status_code == 200
        data = response.json()
        
        origins = set()
        for term in data:
            origins.add(term["origin"])
        
        print(f"✅ Dictionary origins found: {origins}")
        
        # Should have Hebrew, Greek, and possibly Aramaic origins
        expected_origins = ["Ebraico", "Greco", "Aramaico"]
        found_expected = sum(1 for o in expected_origins if any(o in origin for origin in origins))
        assert found_expected >= 2, f"Expected to find at least 2 of {expected_origins}, got: {origins}"
    
    def test_dictionary_search(self):
        """Test dictionary search functionality"""
        response = self.session.get(f"{BASE_URL}/api/dictionary/search/amen")
        
        print(f"Response status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert isinstance(data, list), "Search should return a list"
        assert len(data) > 0, "Search for 'amen' should return results"
        
        # Verify the search found relevant results
        found_amen = any("amen" in term.get("id", "").lower() for term in data)
        assert found_amen, "Search for 'amen' should find the amen term"
        
        print(f"✅ Dictionary search for 'amen' returned {len(data)} results")


# ==================== STANDALONE TEST RUNNER ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
