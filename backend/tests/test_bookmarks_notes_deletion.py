"""
Test suite for bookmark and note deletion features
Tests:
- DELETE /api/bookmarks/{id}
- DELETE /api/bible/study/notes/{id}
- GET /api/bookmarks
- GET /api/bible/study/notes
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

class TestBookmarksAndNotesDeletion:
    """Test bookmark and note deletion APIs"""
    
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
        return data.get("session_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }

    # ============== BOOKMARKS TESTS ==============
    
    def test_create_bookmark(self, auth_headers):
        """Test creating a new bookmark"""
        unique_id = str(uuid.uuid4())[:8]
        bookmark_data = {
            "book": "Genesi",
            "chapter": 1,
            "verse": 1,
            "text": f"Test verse text {unique_id}",
            "note": f"Test note for bookmark {unique_id}",
            "highlight_color": "#D4A574"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/bookmarks",
            json=bookmark_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create bookmark failed: {response.text}"
        data = response.json()
        assert "bookmark_id" in data or "status" in data, "Response should contain bookmark_id or status"
        print(f"✓ Created bookmark successfully: {data}")
        return data
    
    def test_get_bookmarks_list(self, auth_headers):
        """Test getting list of bookmarks"""
        response = requests.get(
            f"{BASE_URL}/api/bookmarks",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Get bookmarks failed: {response.text}"
        bookmarks = response.json()
        assert isinstance(bookmarks, list), "Bookmarks should be a list"
        print(f"✓ Got {len(bookmarks)} bookmarks")
        return bookmarks
    
    def test_create_and_delete_bookmark(self, auth_headers):
        """Test creating a bookmark and then deleting it"""
        # Step 1: Create a bookmark
        unique_id = str(uuid.uuid4())[:8]
        bookmark_data = {
            "book": "Esodo",
            "chapter": 20,
            "verse": 1,
            "text": f"Delete test verse {unique_id}",
            "note": f"This bookmark will be deleted {unique_id}",
            "highlight_color": "#E74C3C"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/bookmarks",
            json=bookmark_data,
            headers=auth_headers
        )
        
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        created_data = create_response.json()
        print(f"✓ Created bookmark for deletion test: {created_data}")
        
        # Step 2: Get bookmarks to find the one we just created
        list_response = requests.get(
            f"{BASE_URL}/api/bookmarks",
            headers=auth_headers
        )
        assert list_response.status_code == 200
        bookmarks = list_response.json()
        
        # Find our bookmark by matching the unique text
        target_bookmark = None
        for bm in bookmarks:
            if unique_id in bm.get("text", "") or unique_id in bm.get("note", ""):
                target_bookmark = bm
                break
        
        assert target_bookmark is not None, f"Could not find created bookmark with id {unique_id}"
        bookmark_id = target_bookmark.get("bookmark_id")
        print(f"✓ Found bookmark_id: {bookmark_id}")
        
        # Step 3: Delete the bookmark
        delete_response = requests.delete(
            f"{BASE_URL}/api/bookmarks/{bookmark_id}",
            headers=auth_headers
        )
        
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        print(f"✓ Deleted bookmark {bookmark_id} successfully")
        
        # Step 4: Verify deletion - bookmark should not be in the list
        verify_response = requests.get(
            f"{BASE_URL}/api/bookmarks",
            headers=auth_headers
        )
        assert verify_response.status_code == 200
        remaining_bookmarks = verify_response.json()
        
        deleted_still_exists = any(bm.get("bookmark_id") == bookmark_id for bm in remaining_bookmarks)
        assert not deleted_still_exists, f"Bookmark {bookmark_id} still exists after deletion"
        print(f"✓ Verified bookmark {bookmark_id} no longer exists")
    
    def test_delete_nonexistent_bookmark(self, auth_headers):
        """Test deleting a bookmark that doesn't exist"""
        fake_bookmark_id = "nonexistent_bookmark_123456"
        
        response = requests.delete(
            f"{BASE_URL}/api/bookmarks/{fake_bookmark_id}",
            headers=auth_headers
        )
        
        # Should return 404 or an error
        assert response.status_code in [404, 400], f"Expected 404/400 for nonexistent bookmark, got {response.status_code}"
        print(f"✓ Correctly returned {response.status_code} for nonexistent bookmark")

    # ============== NOTES TESTS ==============
    
    def test_create_study_note(self, auth_headers):
        """Test creating a new study note"""
        unique_id = str(uuid.uuid4())[:8]
        note_data = {
            "book": "Salmi",
            "chapter": 23,
            "verse": 1,
            "note": f"Test study note content {unique_id}",
            "highlight_color": "#3498DB",
            "tags": ["test", "psalm"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/bible/study/notes",
            json=note_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create note failed: {response.text}"
        data = response.json()
        assert "note_id" in data or "status" in data, "Response should contain note_id or status"
        print(f"✓ Created study note successfully: {data}")
        return data
    
    def test_get_study_notes_list(self, auth_headers):
        """Test getting list of study notes"""
        response = requests.get(
            f"{BASE_URL}/api/bible/study/notes",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Get notes failed: {response.text}"
        notes = response.json()
        assert isinstance(notes, list), "Notes should be a list"
        print(f"✓ Got {len(notes)} study notes")
        return notes
    
    def test_create_and_delete_study_note(self, auth_headers):
        """Test creating a study note and then deleting it"""
        # Step 1: Create a note
        unique_id = str(uuid.uuid4())[:8]
        note_data = {
            "book": "Proverbi",
            "chapter": 3,
            "verse": 5,
            "note": f"Note to be deleted {unique_id}",
            "highlight_color": "#2ECC71",
            "tags": ["delete-test"]
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/bible/study/notes",
            json=note_data,
            headers=auth_headers
        )
        
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        created_data = create_response.json()
        print(f"✓ Created note for deletion test: {created_data}")
        
        # Step 2: Get notes to find the one we just created
        list_response = requests.get(
            f"{BASE_URL}/api/bible/study/notes",
            headers=auth_headers
        )
        assert list_response.status_code == 200
        notes = list_response.json()
        
        # Find our note by matching the unique text
        target_note = None
        for note in notes:
            if unique_id in note.get("note", ""):
                target_note = note
                break
        
        assert target_note is not None, f"Could not find created note with id {unique_id}"
        note_id = target_note.get("note_id")
        print(f"✓ Found note_id: {note_id}")
        
        # Step 3: Delete the note
        delete_response = requests.delete(
            f"{BASE_URL}/api/bible/study/notes/{note_id}",
            headers=auth_headers
        )
        
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        print(f"✓ Deleted note {note_id} successfully")
        
        # Step 4: Verify deletion - note should not be in the list
        verify_response = requests.get(
            f"{BASE_URL}/api/bible/study/notes",
            headers=auth_headers
        )
        assert verify_response.status_code == 200
        remaining_notes = verify_response.json()
        
        deleted_still_exists = any(n.get("note_id") == note_id for n in remaining_notes)
        assert not deleted_still_exists, f"Note {note_id} still exists after deletion"
        print(f"✓ Verified note {note_id} no longer exists")
    
    def test_delete_nonexistent_note(self, auth_headers):
        """Test deleting a note that doesn't exist"""
        fake_note_id = "nonexistent_note_123456"
        
        response = requests.delete(
            f"{BASE_URL}/api/bible/study/notes/{fake_note_id}",
            headers=auth_headers
        )
        
        # Should return 404 or an error
        assert response.status_code in [404, 400], f"Expected 404/400 for nonexistent note, got {response.status_code}"
        print(f"✓ Correctly returned {response.status_code} for nonexistent note")

    # ============== CLEANUP TESTS ==============
    
    def test_cleanup_test_bookmarks(self, auth_headers):
        """Cleanup: Remove test bookmarks created during testing"""
        response = requests.get(
            f"{BASE_URL}/api/bookmarks",
            headers=auth_headers
        )
        
        if response.status_code != 200:
            print("Could not get bookmarks for cleanup")
            return
        
        bookmarks = response.json()
        deleted_count = 0
        
        for bm in bookmarks:
            text = bm.get("text", "")
            note = bm.get("note", "")
            if "Test" in text or "Test" in note or "delete" in text.lower() or "delete" in note.lower():
                bookmark_id = bm.get("bookmark_id")
                if bookmark_id:
                    delete_response = requests.delete(
                        f"{BASE_URL}/api/bookmarks/{bookmark_id}",
                        headers=auth_headers
                    )
                    if delete_response.status_code == 200:
                        deleted_count += 1
        
        print(f"✓ Cleanup: Deleted {deleted_count} test bookmarks")
    
    def test_cleanup_test_notes(self, auth_headers):
        """Cleanup: Remove test notes created during testing"""
        response = requests.get(
            f"{BASE_URL}/api/bible/study/notes",
            headers=auth_headers
        )
        
        if response.status_code != 200:
            print("Could not get notes for cleanup")
            return
        
        notes = response.json()
        deleted_count = 0
        
        for note in notes:
            content = note.get("note", "")
            if "Test" in content or "delete" in content.lower():
                note_id = note.get("note_id")
                if note_id:
                    delete_response = requests.delete(
                        f"{BASE_URL}/api/bible/study/notes/{note_id}",
                        headers=auth_headers
                    )
                    if delete_response.status_code == 200:
                        deleted_count += 1
        
        print(f"✓ Cleanup: Deleted {deleted_count} test notes")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
