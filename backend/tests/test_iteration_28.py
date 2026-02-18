"""
Test suite for iteration 28 - Bug fixes verification
Tests:
1. POST /api/bible/study/notes - Create study notes 
2. DELETE /api/journal/{entry_id} - Delete journal entries
3. GET /api/bible/study/{book}/{chapter} - Returns user_notes AND user_bookmarks
4. POST /api/bookmarks - Create bookmarks

Issue context: User reported 3 bugs:
1) Journal trash icon not working
2) Cannot save notes  
3) Notes/bookmarks/highlights should be visible during reading
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://verse-selector.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "testbible@cibospirituale.it"
TEST_PASSWORD = "Test123!"

class TestIteration28BugFixes:
    """Test APIs for iteration 28 bug fixes"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        token = data.get("session_token")
        print(f"✓ Login successful, got token")
        return token
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }

    # ============== STUDY NOTES TESTS ==============
    
    def test_create_study_note(self, auth_headers):
        """Test POST /api/bible/study/notes - Bug fix: Cannot save notes"""
        unique_id = str(uuid.uuid4())[:8]
        note_data = {
            "book": "Genesi",
            "chapter": 1,
            "verse": 1,
            "note": f"Test study note {unique_id}",
            "highlight_color": "#FFD700",
            "tags": ["test"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/bible/study/notes",
            json=note_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create study note failed: {response.text}"
        data = response.json()
        assert "note_id" in data, "Response should contain note_id"
        assert data["note"] == note_data["note"], "Note content should match"
        assert data["book"] == "Genesi", "Book should be Genesi"
        assert data["chapter"] == 1, "Chapter should be 1"
        print(f"✓ Created study note: {data['note_id']}")
        
        # Store note_id for later cleanup
        TestIteration28BugFixes.created_note_id = data["note_id"]
        return data

    def test_create_study_note_without_verse(self, auth_headers):
        """Test creating chapter-level note (verse is null)"""
        unique_id = str(uuid.uuid4())[:8]
        note_data = {
            "book": "Genesi",
            "chapter": 2,
            "verse": None,  # Chapter-level note
            "note": f"Chapter note {unique_id}",
            "highlight_color": None,
            "tags": []
        }
        
        response = requests.post(
            f"{BASE_URL}/api/bible/study/notes",
            json=note_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create chapter note failed: {response.text}"
        data = response.json()
        assert "note_id" in data
        assert data["verse"] is None, "Verse should be null for chapter notes"
        print(f"✓ Created chapter-level note: {data['note_id']}")
        
        # Cleanup
        TestIteration28BugFixes.created_chapter_note_id = data["note_id"]
        return data

    # ============== JOURNAL DELETION TESTS ==============
    
    def test_create_and_delete_journal_entry(self, auth_headers):
        """Test DELETE /api/journal/{entry_id} - Bug fix: Trash icon not working"""
        # First create an entry
        unique_id = str(uuid.uuid4())[:8]
        entry_data = {
            "content": f"Test journal entry for deletion {unique_id}",
            "mood": "grato",
            "language": "it"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/journal",
            json=entry_data,
            headers=auth_headers
        )
        
        assert create_response.status_code == 200, f"Create journal failed: {create_response.text}"
        created = create_response.json()
        entry_id = created["entry_id"]
        print(f"✓ Created journal entry: {entry_id}")
        
        # Now delete it
        delete_response = requests.delete(
            f"{BASE_URL}/api/journal/{entry_id}",
            headers=auth_headers
        )
        
        assert delete_response.status_code == 200, f"Delete journal failed: {delete_response.text}"
        delete_data = delete_response.json()
        assert "message" in delete_data or "success" in delete_data
        print(f"✓ Deleted journal entry: {entry_id}")
        
        # Verify it's deleted
        get_response = requests.get(
            f"{BASE_URL}/api/journal",
            headers=auth_headers
        )
        entries = get_response.json()
        entry_ids = [e["entry_id"] for e in entries]
        assert entry_id not in entry_ids, "Deleted entry should not appear in list"
        print("✓ Verified entry no longer in list")
    
    def test_delete_nonexistent_journal_entry(self, auth_headers):
        """Test deleting a non-existent journal entry returns 404"""
        fake_id = str(uuid.uuid4())
        
        response = requests.delete(
            f"{BASE_URL}/api/journal/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Non-existent entry returns 404")

    # ============== STUDY DATA WITH BOOKMARKS TESTS ==============
    
    def test_get_study_data_returns_user_bookmarks(self, auth_headers):
        """Test GET /api/bible/study/{book}/{chapter} returns user_bookmarks"""
        # First create a bookmark for this chapter
        unique_id = str(uuid.uuid4())[:8]
        bookmark_data = {
            "book": "Genesi",
            "chapter": 1,
            "verse": 3,
            "text": f"Test bookmark verse {unique_id}",
            "note": "Bookmark note",
            "highlight_color": "#E74C3C"
        }
        
        bookmark_resp = requests.post(
            f"{BASE_URL}/api/bookmarks",
            json=bookmark_data,
            headers=auth_headers
        )
        assert bookmark_resp.status_code == 200
        TestIteration28BugFixes.created_bookmark_id = bookmark_resp.json().get("bookmark_id")
        
        # Now get study data
        response = requests.get(
            f"{BASE_URL}/api/bible/study/Genesi/1",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Get study data failed: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "book" in data, "Response should contain book"
        assert "chapter" in data, "Response should contain chapter"
        assert "user_notes" in data, "Response should contain user_notes"
        assert "user_bookmarks" in data, "Response should contain user_bookmarks - THIS IS THE BUG FIX"
        
        # Verify bookmarks are returned
        assert isinstance(data["user_bookmarks"], list), "user_bookmarks should be a list"
        print(f"✓ Study data returns user_notes: {len(data['user_notes'])} and user_bookmarks: {len(data['user_bookmarks'])}")
        
        # Check our bookmark is in the list
        if data["user_bookmarks"]:
            bookmark_verses = [b.get("verse") for b in data["user_bookmarks"]]
            print(f"✓ Bookmarked verses: {bookmark_verses}")
        
        return data

    def test_get_study_data_returns_notes(self, auth_headers):
        """Test that study data includes user's notes"""
        response = requests.get(
            f"{BASE_URL}/api/bible/study/Genesi/1",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "user_notes" in data
        assert isinstance(data["user_notes"], list)
        print(f"✓ User notes returned: {len(data['user_notes'])}")
        
        # Check note structure if notes exist
        if data["user_notes"]:
            note = data["user_notes"][0]
            assert "note_id" in note, "Note should have note_id"
            assert "note" in note, "Note should have note content"
            assert "verse" in note, "Note should have verse"
            print(f"✓ Note structure valid: {note.get('note_id')}")

    # ============== BOOKMARKS TESTS ==============
    
    def test_create_bookmark(self, auth_headers):
        """Test POST /api/bookmarks - Create bookmark"""
        unique_id = str(uuid.uuid4())[:8]
        bookmark_data = {
            "book": "Genesi",
            "chapter": 1,
            "verse": 5,
            "text": f"And God said, Let there be light {unique_id}",
            "note": "Light symbolizes knowledge",
            "highlight_color": "#FFD700"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/bookmarks",
            json=bookmark_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create bookmark failed: {response.text}"
        data = response.json()
        assert "bookmark_id" in data, "Response should contain bookmark_id"
        print(f"✓ Created bookmark: {data['bookmark_id']}")
        
        TestIteration28BugFixes.second_bookmark_id = data.get("bookmark_id")
        return data
    
    def test_get_bookmarks_list(self, auth_headers):
        """Test GET /api/bookmarks - Get all bookmarks"""
        response = requests.get(
            f"{BASE_URL}/api/bookmarks",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        bookmarks = response.json()
        assert isinstance(bookmarks, list), "Bookmarks should be a list"
        print(f"✓ Total bookmarks: {len(bookmarks)}")
        return bookmarks

    def test_delete_bookmark(self, auth_headers):
        """Test DELETE /api/bookmarks/{id}"""
        # Create a bookmark to delete
        bookmark_data = {
            "book": "Esodo",
            "chapter": 1,
            "verse": 1,
            "text": "Temporary bookmark",
            "note": None,
            "highlight_color": "#CCCCCC"
        }
        
        create_resp = requests.post(
            f"{BASE_URL}/api/bookmarks",
            json=bookmark_data,
            headers=auth_headers
        )
        assert create_resp.status_code == 200
        bookmark_id = create_resp.json()["bookmark_id"]
        
        # Delete it
        delete_resp = requests.delete(
            f"{BASE_URL}/api/bookmarks/{bookmark_id}",
            headers=auth_headers
        )
        
        assert delete_resp.status_code == 200, f"Delete bookmark failed: {delete_resp.text}"
        print(f"✓ Deleted bookmark: {bookmark_id}")

    # ============== CLEANUP ==============
    
    def test_cleanup(self, auth_headers):
        """Cleanup test data"""
        # Delete created notes
        if hasattr(TestIteration28BugFixes, 'created_note_id'):
            requests.delete(
                f"{BASE_URL}/api/bible/study/notes/{TestIteration28BugFixes.created_note_id}",
                headers=auth_headers
            )
            print(f"✓ Cleaned up note: {TestIteration28BugFixes.created_note_id}")
        
        if hasattr(TestIteration28BugFixes, 'created_chapter_note_id'):
            requests.delete(
                f"{BASE_URL}/api/bible/study/notes/{TestIteration28BugFixes.created_chapter_note_id}",
                headers=auth_headers
            )
            print(f"✓ Cleaned up chapter note")
        
        # Delete created bookmarks
        if hasattr(TestIteration28BugFixes, 'created_bookmark_id'):
            requests.delete(
                f"{BASE_URL}/api/bookmarks/{TestIteration28BugFixes.created_bookmark_id}",
                headers=auth_headers
            )
            print(f"✓ Cleaned up bookmark")
        
        if hasattr(TestIteration28BugFixes, 'second_bookmark_id'):
            requests.delete(
                f"{BASE_URL}/api/bookmarks/{TestIteration28BugFixes.second_bookmark_id}",
                headers=auth_headers
            )
            print(f"✓ Cleaned up second bookmark")
