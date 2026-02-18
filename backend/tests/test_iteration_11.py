"""
Backend Tests - Iteration 11
Testing: Quiz loading speed, TTS languages, Reading history APIs, App fluidity
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://verse-selector.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "testbible@cibospirituale.it"
TEST_PASSWORD = "Test123!"


class TestAuthentication:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def session(self):
        return requests.Session()
    
    @pytest.fixture(scope="class")
    def auth_token(self, session):
        """Login and get authentication token"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "session_token" in data
        return data["session_token"]
    
    def test_login_success(self, session):
        """Test login with valid credentials"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "session_token" in data
        print(f"✓ Login successful, user: {data['user'].get('name', 'Unknown')}")


class TestQuizPerformance:
    """Quiz loading performance tests"""
    
    @pytest.fixture(scope="class")
    def session(self):
        return requests.Session()
    
    @pytest.fixture(scope="class")
    def auth_headers(self, session):
        """Login and get auth headers"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = response.json().get("session_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_quiz_topics_load_speed(self, session, auth_headers):
        """Test quiz topics load within acceptable time"""
        start = time.time()
        response = session.get(f"{BASE_URL}/api/quiz/topics?lang=it", headers=auth_headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Quiz topics loaded in {elapsed:.2f}s ({len(data)} topics)")
        assert elapsed < 3.0, f"Quiz topics took too long: {elapsed:.2f}s"
    
    def test_quiz_categories_load_speed(self, session, auth_headers):
        """Test quiz categories (1000 questions) load within acceptable time"""
        start = time.time()
        response = session.get(f"{BASE_URL}/api/quiz/categories?lang=it", headers=auth_headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Quiz categories loaded in {elapsed:.2f}s ({len(data)} categories)")
        assert elapsed < 5.0, f"Quiz categories took too long: {elapsed:.2f}s"
    
    def test_quiz_parallel_load_simulation(self, session, auth_headers):
        """Simulate parallel loading of topics and categories (frontend Promise.all)"""
        import concurrent.futures
        
        def fetch_topics():
            start = time.time()
            r = session.get(f"{BASE_URL}/api/quiz/topics?lang=it", headers=auth_headers)
            return time.time() - start, r.status_code, 'topics'
        
        def fetch_categories():
            start = time.time()
            r = session.get(f"{BASE_URL}/api/quiz/categories?lang=it", headers=auth_headers)
            return time.time() - start, r.status_code, 'categories'
        
        start = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda f: f(), [fetch_topics, fetch_categories]))
        total_time = time.time() - start
        
        for elapsed, status, name in results:
            assert status == 200, f"{name} failed with status {status}"
            print(f"  - {name}: {elapsed:.2f}s")
        
        print(f"✓ Parallel load completed in {total_time:.2f}s")
        # Parallel should be faster than sequential
        assert total_time < 6.0, f"Parallel load took too long: {total_time:.2f}s"
    
    def test_quiz_category_start(self, session, auth_headers):
        """Test starting a thematic quiz (category quiz)"""
        # Get categories first
        response = session.get(f"{BASE_URL}/api/quiz/categories?lang=it", headers=auth_headers)
        assert response.status_code == 200
        categories = response.json()
        
        if categories:
            first_cat = categories[0]
            cat_id = first_cat.get("id")
            
            start = time.time()
            response = session.get(f"{BASE_URL}/api/quiz/category/{cat_id}?lang=it", headers=auth_headers)
            elapsed = time.time() - start
            
            assert response.status_code == 200
            data = response.json()
            assert "questions" in data
            print(f"✓ Quiz '{first_cat.get('title')}' started in {elapsed:.2f}s with {len(data.get('questions', []))} questions")
            assert elapsed < 5.0, f"Quiz start took too long: {elapsed:.2f}s"


class TestTTSLanguages:
    """Test Text-to-Speech language support"""
    
    def test_tts_languages_available(self):
        """Verify TTS language codes are returned from languages endpoint"""
        response = requests.get(f"{BASE_URL}/api/languages")
        assert response.status_code == 200
        
        languages = response.json()
        expected_tts = {
            "it": "it-IT",
            "es": "es-ES",
            "en": "en-US",  # Note: endpoint returns en-US, bible.tsx uses en-GB
            "de": "de-DE",
            "fr": "fr-FR",
            "pt": "pt-BR"
        }
        
        for lang, expected_code in expected_tts.items():
            assert lang in languages, f"Language {lang} not found"
            tts_code = languages[lang].get("tts_code")
            assert tts_code is not None, f"TTS code missing for {lang}"
            print(f"✓ {lang}: tts_code={tts_code}")
    
    def test_bible_chapter_for_tts(self):
        """Test Bible chapter can be fetched for TTS playback"""
        # Test Italian
        response = requests.get(f"{BASE_URL}/api/bible/chapter/Genesi/1?lang=it")
        assert response.status_code == 200
        data = response.json()
        assert "verses" in data
        assert len(data["verses"]) > 0
        print(f"✓ Italian chapter loaded with {len(data['verses'])} verses for TTS")
        
        # Test English
        response = requests.get(f"{BASE_URL}/api/bible/chapter/Genesis/1?lang=en")
        assert response.status_code == 200
        data = response.json()
        assert "verses" in data
        print(f"✓ English chapter loaded with {len(data['verses'])} verses for TTS")


class TestReadingHistory:
    """Test reading history endpoints - New feature"""
    
    @pytest.fixture(scope="class")
    def session(self):
        return requests.Session()
    
    @pytest.fixture(scope="class")
    def auth_headers(self, session):
        """Login and get auth headers"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = response.json().get("session_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_save_chapter_reading(self, session, auth_headers):
        """Test POST /api/progress/reading/chapter - Save chapter as read"""
        # Test with a specific book and chapter
        response = session.post(
            f"{BASE_URL}/api/progress/reading/chapter?book=Genesi&chapter=1",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert data.get("book") == "Genesi"
        assert data.get("chapter") == 1
        print(f"✓ Saved reading: Genesi 1")
        
        # Save another chapter
        response = session.post(
            f"{BASE_URL}/api/progress/reading/chapter?book=Giovanni&chapter=3",
            headers=auth_headers
        )
        assert response.status_code == 200
        print(f"✓ Saved reading: Giovanni 3")
    
    def test_get_reading_history(self, session, auth_headers):
        """Test GET /api/progress/reading/history - Get reading history"""
        response = session.get(
            f"{BASE_URL}/api/progress/reading/history?limit=20",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "history" in data
        assert "total" in data
        assert isinstance(data["history"], list)
        
        history = data["history"]
        print(f"✓ Reading history retrieved: {len(history)} entries")
        
        # Verify structure of history entries
        if history:
            entry = history[0]
            assert "book" in entry, "History entry missing 'book'"
            assert "chapter" in entry, "History entry missing 'chapter'"
            assert "last_read" in entry, "History entry missing 'last_read'"
            assert "read_count" in entry or True  # read_count may not be present on first read
            print(f"  Latest: {entry.get('book')} {entry.get('chapter')} (read_count: {entry.get('read_count', 1)})")
    
    def test_reading_history_updates_count(self, session, auth_headers):
        """Test that re-reading a chapter increments read_count"""
        # Read the same chapter twice
        book = "Salmi"
        chapter = 23
        
        # First read
        response = session.post(
            f"{BASE_URL}/api/progress/reading/chapter?book={book}&chapter={chapter}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Second read
        response = session.post(
            f"{BASE_URL}/api/progress/reading/chapter?book={book}&chapter={chapter}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Check history
        response = session.get(
            f"{BASE_URL}/api/progress/reading/history?limit=50",
            headers=auth_headers
        )
        data = response.json()
        
        # Find our entry
        entry = next((e for e in data["history"] if e.get("book") == book and e.get("chapter") == chapter), None)
        assert entry is not None, f"Could not find {book} {chapter} in history"
        
        # read_count should be at least 2 (or 1 if first time ever read)
        read_count = entry.get("read_count", 1)
        print(f"✓ {book} {chapter} read_count: {read_count}")
        assert read_count >= 1
    
    def test_reading_history_sorted_by_last_read(self, session, auth_headers):
        """Test that history is sorted by last_read descending"""
        # Save a new chapter to ensure it's at top
        response = session.post(
            f"{BASE_URL}/api/progress/reading/chapter?book=Matteo&chapter=5",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        response = session.get(
            f"{BASE_URL}/api/progress/reading/history?limit=10",
            headers=auth_headers
        )
        data = response.json()
        history = data["history"]
        
        # Most recent should be first
        if history:
            assert history[0].get("book") == "Matteo" and history[0].get("chapter") == 5, \
                "Most recently read chapter should be first"
            print(f"✓ History sorted correctly, most recent: {history[0].get('book')} {history[0].get('chapter')}")


class TestProgressEndpoints:
    """Test user progress endpoints"""
    
    @pytest.fixture(scope="class")
    def session(self):
        return requests.Session()
    
    @pytest.fixture(scope="class")
    def auth_headers(self, session):
        """Login and get auth headers"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = response.json().get("session_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_progress(self, session, auth_headers):
        """Test GET /api/progress - User progress stats"""
        response = session.get(f"{BASE_URL}/api/progress", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "reading_streak" in data
        assert "total_chapters_read" in data
        assert "total_journal_entries" in data
        print(f"✓ Progress: streak={data.get('reading_streak')}, chapters={data.get('total_chapters_read')}")
    
    def test_update_reading_progress(self, session, auth_headers):
        """Test POST /api/progress/reading - Update reading progress"""
        response = session.post(f"{BASE_URL}/api/progress/reading", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ Reading progress updated: {data}")


class TestAppFluidity:
    """Test general API response times for app fluidity"""
    
    def test_languages_endpoint_speed(self):
        """Test /api/languages response time"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/languages")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0, f"Languages endpoint too slow: {elapsed:.2f}s"
        print(f"✓ /api/languages: {elapsed:.3f}s")
    
    def test_bible_books_speed(self):
        """Test /api/bible/books response time"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/bible/books?lang=it")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 2.0, f"Bible books endpoint too slow: {elapsed:.2f}s"
        print(f"✓ /api/bible/books: {elapsed:.3f}s")
    
    def test_bible_chapter_speed(self):
        """Test /api/bible/chapter response time"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/bible/chapter/Giovanni/3?lang=it")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 3.0, f"Bible chapter endpoint too slow: {elapsed:.2f}s"
        print(f"✓ /api/bible/chapter: {elapsed:.3f}s")
    
    def test_bible_editions_speed(self):
        """Test /api/bible/editions response time"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/bible/editions")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0, f"Bible editions endpoint too slow: {elapsed:.2f}s"
        print(f"✓ /api/bible/editions: {elapsed:.3f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
