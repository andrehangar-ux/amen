"""
Iteration 24 Tests - Testing new features:
1. Mood-checkin API returns different verses on each call (not daily rotation)
2. Daily-verse API with translation
3. Bookmarks API endpoint
4. Study notes API endpoint
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://verse-mood-check.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "testbible@cibospirituale.it"
TEST_PASSWORD = "Test123!"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip(f"Cannot login: {response.text}")
    return response.json().get("session_token")


@pytest.fixture
def auth_headers(auth_token):
    """Headers with authentication"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestMoodCheckinRandomVerses:
    """Test that mood-checkin returns different verses on consecutive calls"""
    
    def test_mood_checkin_returns_different_verses(self, auth_headers):
        """Verify verse changes on each tap/call (not daily rotation)"""
        verse_refs = []
        mood = "ansioso"  # Testing with 'anxious' mood which has multiple verses
        
        # Make 5 consecutive calls
        for i in range(5):
            response = requests.post(
                f"{BASE_URL}/api/ai/mood-checkin",
                json={"mood": mood, "language": "it"},
                headers=auth_headers,
                timeout=30
            )
            assert response.status_code == 200, f"Call {i+1} failed: {response.text}"
            
            data = response.json()
            assert "verse" in data, "Response missing 'verse' field"
            assert "ref" in data["verse"], "Verse missing 'ref' field"
            verse_refs.append(data["verse"]["ref"])
            
            # Small delay between calls
            time.sleep(0.5)
        
        # Check that we got at least 2 different verses in 5 calls
        # (probability of same verse 5 times with 6+ options is very low)
        unique_refs = set(verse_refs)
        print(f"Verse references collected: {verse_refs}")
        print(f"Unique verses: {len(unique_refs)}")
        
        # With random selection, we expect at least 2 different verses in 5 calls
        assert len(unique_refs) >= 2, f"Expected different verses but got same verse 5 times: {verse_refs}"
    
    def test_mood_checkin_happy_mood(self, auth_headers):
        """Test happy mood returns verse with reflection"""
        response = requests.post(
            f"{BASE_URL}/api/ai/mood-checkin",
            json={"mood": "felice", "language": "it"},
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "mood" in data
        assert data["mood"] == "felice"
        assert "verse" in data
        assert "ref" in data["verse"]
        assert "text" in data["verse"]
        assert "reflection" in data
        print(f"Happy mood verse: {data['verse']['ref']}")
    
    def test_mood_checkin_sad_mood(self, auth_headers):
        """Test sad mood returns verse with reflection"""
        response = requests.post(
            f"{BASE_URL}/api/ai/mood-checkin",
            json={"mood": "triste", "language": "en"},
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["mood"] == "triste"
        assert "verse" in data
        # English verse should be returned
        print(f"Sad mood verse (EN): {data['verse']['ref']}")
    
    def test_mood_checkin_multilingual(self, auth_headers):
        """Test mood checkin works in multiple languages"""
        languages = ["it", "en", "es"]
        
        for lang in languages:
            response = requests.post(
                f"{BASE_URL}/api/ai/mood-checkin",
                json={"mood": "speranzoso", "language": lang},
                headers=auth_headers,
                timeout=30
            )
            assert response.status_code == 200, f"Failed for language {lang}"
            data = response.json()
            assert "verse" in data
            print(f"Language {lang}: {data['verse']['ref']}")


class TestDailyVerseAPI:
    """Test daily verse endpoint with translation"""
    
    def test_daily_verse_italian(self, auth_headers):
        """Test daily verse in Italian"""
        response = requests.get(
            f"{BASE_URL}/api/bible/daily-verse?lang=it",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        # API returns: text, reference, language
        assert "text" in data
        assert "reference" in data
        assert "language" in data
        assert data["language"] == "it"
        print(f"Daily verse IT: {data['reference']} - {data['text'][:50]}...")
    
    def test_daily_verse_english(self, auth_headers):
        """Test daily verse in English"""
        response = requests.get(
            f"{BASE_URL}/api/bible/daily-verse?lang=en",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "text" in data
        assert "reference" in data
        assert data["language"] == "en"
        print(f"Daily verse EN: {data['reference']} - {data['text'][:50]}...")
    
    def test_daily_verse_spanish(self, auth_headers):
        """Test daily verse in Spanish"""
        response = requests.get(
            f"{BASE_URL}/api/bible/daily-verse?lang=es",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "text" in data
        assert "reference" in data
        assert data["language"] == "es"
        print(f"Daily verse ES: {data['reference']} - {data['text'][:50]}...")


class TestBookmarksAPI:
    """Test bookmarks endpoints"""
    
    def test_get_bookmarks(self, auth_headers):
        """Test fetching user bookmarks"""
        response = requests.get(
            f"{BASE_URL}/api/bookmarks",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Bookmarks should return a list"
        print(f"Found {len(data)} bookmarks")
    
    def test_create_and_delete_bookmark(self, auth_headers):
        """Test creating and deleting a bookmark"""
        # Create bookmark
        new_bookmark = {
            "book": "TEST_Salmi",
            "chapter": 23,
            "verse": 1,
            "text": "L'Eterno è il mio pastore, nulla mi mancherà.",
            "note": "Test bookmark note",
            "highlight_color": "#4A7C59"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/bookmarks",
            json=new_bookmark,
            headers=auth_headers
        )
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        
        created = create_response.json()
        assert "bookmark_id" in created
        bookmark_id = created["bookmark_id"]
        print(f"Created bookmark: {bookmark_id}")
        
        # Verify bookmark appears in list
        get_response = requests.get(
            f"{BASE_URL}/api/bookmarks",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        bookmarks = get_response.json()
        assert any(b["bookmark_id"] == bookmark_id for b in bookmarks), "New bookmark not in list"
        
        # Delete bookmark
        delete_response = requests.delete(
            f"{BASE_URL}/api/bookmarks/{bookmark_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        print(f"Deleted bookmark: {bookmark_id}")
        
        # Verify deletion
        get_after_delete = requests.get(
            f"{BASE_URL}/api/bookmarks",
            headers=auth_headers
        )
        bookmarks_after = get_after_delete.json()
        assert not any(b["bookmark_id"] == bookmark_id for b in bookmarks_after), "Bookmark still exists"


class TestStudyNotesAPI:
    """Test study notes endpoints"""
    
    def test_get_all_study_notes(self, auth_headers):
        """Test fetching all user study notes"""
        response = requests.get(
            f"{BASE_URL}/api/bible/study/notes",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Study notes should return a list"
        print(f"Found {len(data)} study notes")
    
    def test_create_and_delete_study_note(self, auth_headers):
        """Test creating and deleting a study note"""
        # Create note
        new_note = {
            "book": "TEST_Giovanni",
            "chapter": 3,
            "verse": 16,
            "note": "Test study note for iteration 24",
            "highlight_color": "#E91E63",
            "tags": ["test", "iteration24"]
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/bible/study/notes",
            json=new_note,
            headers=auth_headers
        )
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        
        created = create_response.json()
        assert "note_id" in created
        note_id = created["note_id"]
        print(f"Created study note: {note_id}")
        
        # Verify note appears in list
        get_response = requests.get(
            f"{BASE_URL}/api/bible/study/notes",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        notes = get_response.json()
        assert any(n["note_id"] == note_id for n in notes), "New note not in list"
        
        # Delete note
        delete_response = requests.delete(
            f"{BASE_URL}/api/bible/study/notes/{note_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        print(f"Deleted study note: {note_id}")
        
        # Verify deletion
        get_after_delete = requests.get(
            f"{BASE_URL}/api/bible/study/notes",
            headers=auth_headers
        )
        notes_after = get_after_delete.json()
        assert not any(n["note_id"] == note_id for n in notes_after), "Note still exists"


class TestMyContentIntegration:
    """Test the integration of My Content feature components"""
    
    def test_all_content_types_accessible(self, auth_headers):
        """Verify all content types (bookmarks, notes) are accessible"""
        # Get bookmarks
        bookmarks_response = requests.get(
            f"{BASE_URL}/api/bookmarks",
            headers=auth_headers
        )
        assert bookmarks_response.status_code == 200
        
        # Get study notes
        notes_response = requests.get(
            f"{BASE_URL}/api/bible/study/notes",
            headers=auth_headers
        )
        assert notes_response.status_code == 200
        
        bookmarks = bookmarks_response.json()
        notes = notes_response.json()
        
        print(f"Content Summary: {len(bookmarks)} bookmarks, {len(notes)} notes")
        
        # Both endpoints should return lists
        assert isinstance(bookmarks, list)
        assert isinstance(notes, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
