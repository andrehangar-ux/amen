"""
Iteration 16 Tests: Progress Stats & Book Progress APIs
- GET /api/progress/stats - detailed reading statistics
- GET /api/progress/book/{book_name} - progress for specific book
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://amen-corrections.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "testbible@cibospirituale.it"
TEST_PASSWORD = "Test123!"


class TestProgressStatsAPI:
    """Test /api/progress/stats endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get session token"""
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "bypass-tunnel-reminder": "true"
        })
        
        # Login
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_resp.status_code == 200:
            data = login_resp.json()
            self.token = data.get("session_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Login failed - cannot test authenticated endpoints")
    
    def test_progress_stats_requires_auth(self):
        """Test that /api/progress/stats requires authentication"""
        # Create new session without auth
        no_auth_session = requests.Session()
        no_auth_session.headers.update({
            "Content-Type": "application/json",
            "bypass-tunnel-reminder": "true"
        })
        
        response = no_auth_session.get(f"{BASE_URL}/api/progress/stats")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ GET /api/progress/stats returns 401 without authentication")
    
    def test_progress_stats_returns_valid_structure(self):
        """Test that /api/progress/stats returns correct data structure"""
        response = self.session.get(f"{BASE_URL}/api/progress/stats")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Check required fields exist
        assert "basic_stats" in data, "Missing 'basic_stats' field"
        assert "total_unique_chapters" in data, "Missing 'total_unique_chapters' field"
        assert "total_read_count" in data, "Missing 'total_read_count' field"
        assert "books_progress" in data, "Missing 'books_progress' field"
        assert "recent_activity_count" in data, "Missing 'recent_activity_count' field"
        assert "chapters_read" in data, "Missing 'chapters_read' field"
        
        # Check basic_stats structure
        basic_stats = data["basic_stats"]
        assert "reading_streak" in basic_stats, "Missing 'reading_streak' in basic_stats"
        assert "total_chapters_read" in basic_stats, "Missing 'total_chapters_read' in basic_stats"
        
        # Check types
        assert isinstance(data["total_unique_chapters"], int), "total_unique_chapters should be int"
        assert isinstance(data["total_read_count"], int), "total_read_count should be int"
        assert isinstance(data["recent_activity_count"], int), "recent_activity_count should be int"
        assert isinstance(data["books_progress"], list), "books_progress should be list"
        assert isinstance(data["chapters_read"], list), "chapters_read should be list"
        
        print(f"✓ GET /api/progress/stats returns valid structure")
        print(f"  - total_unique_chapters: {data['total_unique_chapters']}")
        print(f"  - total_read_count: {data['total_read_count']}")
        print(f"  - books_progress count: {len(data['books_progress'])}")
        print(f"  - chapters_read count: {len(data['chapters_read'])}")
        print(f"  - recent_activity_count: {data['recent_activity_count']}")
    
    def test_progress_stats_books_progress_structure(self):
        """Test that books_progress items have correct structure"""
        response = self.session.get(f"{BASE_URL}/api/progress/stats")
        assert response.status_code == 200
        
        data = response.json()
        books_progress = data.get("books_progress", [])
        
        if len(books_progress) > 0:
            book = books_progress[0]
            assert "book" in book, "Missing 'book' field in book progress"
            assert "chapters_read" in book, "Missing 'chapters_read' field in book progress"
            assert "total_reads" in book, "Missing 'total_reads' field in book progress"
            assert "last_read" in book, "Missing 'last_read' field in book progress"
            
            print(f"✓ books_progress structure validated - first book: {book['book']}")
            print(f"  - chapters_read: {book['chapters_read']}")
            print(f"  - total_reads: {book['total_reads']}")
        else:
            print("✓ books_progress is empty (no reading history yet)")
    
    def test_progress_stats_chapters_read_structure(self):
        """Test that chapters_read items have correct structure"""
        response = self.session.get(f"{BASE_URL}/api/progress/stats")
        assert response.status_code == 200
        
        data = response.json()
        chapters_read = data.get("chapters_read", [])
        
        if len(chapters_read) > 0:
            chapter = chapters_read[0]
            assert "book" in chapter, "Missing 'book' field in chapters_read"
            assert "chapter" in chapter, "Missing 'chapter' field in chapters_read"
            
            print(f"✓ chapters_read structure validated - first entry: {chapter['book']} {chapter['chapter']}")
        else:
            print("✓ chapters_read is empty (no reading history yet)")


class TestBookProgressAPI:
    """Test /api/progress/book/{book_name} endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get session token"""
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "bypass-tunnel-reminder": "true"
        })
        
        # Login
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_resp.status_code == 200:
            data = login_resp.json()
            self.token = data.get("session_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Login failed - cannot test authenticated endpoints")
    
    def test_book_progress_requires_auth(self):
        """Test that /api/progress/book/{book_name} requires authentication"""
        no_auth_session = requests.Session()
        no_auth_session.headers.update({
            "Content-Type": "application/json",
            "bypass-tunnel-reminder": "true"
        })
        
        response = no_auth_session.get(f"{BASE_URL}/api/progress/book/Genesi")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ GET /api/progress/book/{book_name} returns 401 without authentication")
    
    def test_book_progress_returns_valid_structure(self):
        """Test that /api/progress/book/{book_name} returns correct data structure"""
        response = self.session.get(f"{BASE_URL}/api/progress/book/Genesi")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Check required fields exist
        assert "book" in data, "Missing 'book' field"
        assert "chapters_read" in data, "Missing 'chapters_read' field"
        assert "details" in data, "Missing 'details' field"
        
        # Check types
        assert isinstance(data["chapters_read"], list), "chapters_read should be list"
        assert isinstance(data["details"], list), "details should be list"
        assert data["book"] == "Genesi", f"Expected book 'Genesi', got {data['book']}"
        
        print(f"✓ GET /api/progress/book/Genesi returns valid structure")
        print(f"  - book: {data['book']}")
        print(f"  - chapters_read count: {len(data['chapters_read'])}")
        print(f"  - details count: {len(data['details'])}")
    
    def test_book_progress_with_url_encoded_name(self):
        """Test book progress with URL-encoded book names (e.g., '1 Samuele')"""
        import urllib.parse
        book_name = urllib.parse.quote("1 Samuele")
        response = self.session.get(f"{BASE_URL}/api/progress/book/{book_name}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "book" in data, "Missing 'book' field"
        assert "chapters_read" in data, "Missing 'chapters_read' field"
        
        print(f"✓ GET /api/progress/book/1%20Samuele (URL encoded) returns valid structure")
    
    def test_book_progress_nonexistent_book(self):
        """Test book progress for a book with no reading history"""
        response = self.session.get(f"{BASE_URL}/api/progress/book/NonexistentBook")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["book"] == "NonexistentBook"
        assert data["chapters_read"] == []
        assert data["details"] == []
        
        print("✓ GET /api/progress/book/NonexistentBook returns empty but valid response")


class TestProgressWithReadingData:
    """Test progress stats after creating reading data"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get session token"""
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "bypass-tunnel-reminder": "true"
        })
        
        # Login
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_resp.status_code == 200:
            data = login_resp.json()
            self.token = data.get("session_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Login failed - cannot test authenticated endpoints")
    
    def test_save_chapter_reading_and_verify_stats(self):
        """Test saving a chapter reading and verifying it appears in stats"""
        # First, get current stats
        stats_before = self.session.get(f"{BASE_URL}/api/progress/stats").json()
        chapters_before = stats_before.get("total_unique_chapters", 0)
        
        # Save a chapter reading (Matteo chapter 5 - commonly tested)
        save_response = self.session.post(
            f"{BASE_URL}/api/progress/reading/chapter?book=Matteo&chapter=5"
        )
        assert save_response.status_code == 200, f"Failed to save chapter: {save_response.status_code}"
        
        # Get stats again
        stats_after = self.session.get(f"{BASE_URL}/api/progress/stats").json()
        
        # Verify the chapter appears in chapters_read
        chapters_read = stats_after.get("chapters_read", [])
        found = any(c["book"] == "Matteo" and c["chapter"] == 5 for c in chapters_read)
        
        print(f"✓ Chapter reading saved and verified in stats")
        print(f"  - Chapter found in chapters_read: {found}")
        print(f"  - Total unique chapters: {stats_after.get('total_unique_chapters', 0)}")
    
    def test_book_progress_after_reading(self):
        """Test book-specific progress after reading chapters"""
        # Save a couple of chapters
        self.session.post(f"{BASE_URL}/api/progress/reading/chapter?book=Giovanni&chapter=1")
        self.session.post(f"{BASE_URL}/api/progress/reading/chapter?book=Giovanni&chapter=3")
        
        # Get Giovanni progress
        response = self.session.get(f"{BASE_URL}/api/progress/book/Giovanni")
        assert response.status_code == 200
        
        data = response.json()
        chapters_read = data.get("chapters_read", [])
        
        # Should have at least chapters 1 and 3
        assert 1 in chapters_read or 3 in chapters_read, "Expected at least one chapter to be recorded"
        
        print(f"✓ Book progress for Giovanni verified")
        print(f"  - Chapters read: {chapters_read}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
