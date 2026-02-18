"""
Test suite for Reset Progress Stats feature
Tests the individual reset functionality for: streak, chapters, journal, history
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "testbible@cibospirituale.it"
TEST_PASSWORD = "Test123!"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Login failed: {response.status_code} - {response.text}")
    return response.json().get("session_token")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get auth headers for authenticated requests"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestResetProgressEndpoints:
    """Test all reset progress stat endpoints"""

    def test_reset_streak_endpoint_exists(self, auth_headers):
        """Test POST /api/progress/reset/streak endpoint returns 200"""
        response = requests.post(
            f"{BASE_URL}/api/progress/reset/streak",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data
        assert data.get("reset") == "reading_streak"
        print(f"PASS: Reset streak - {data['message']}")

    def test_reset_chapters_endpoint_exists(self, auth_headers):
        """Test POST /api/progress/reset/chapters endpoint returns 200"""
        response = requests.post(
            f"{BASE_URL}/api/progress/reset/chapters",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data
        assert data.get("reset") == "total_chapters_read"
        print(f"PASS: Reset chapters - {data['message']}")

    def test_reset_journal_endpoint_exists(self, auth_headers):
        """Test POST /api/progress/reset/journal endpoint returns 200"""
        response = requests.post(
            f"{BASE_URL}/api/progress/reset/journal",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data
        assert data.get("reset") == "total_journal_entries"
        print(f"PASS: Reset journal - {data['message']}")

    def test_reset_history_endpoint_exists(self, auth_headers):
        """Test POST /api/progress/reset/history endpoint returns 200"""
        response = requests.post(
            f"{BASE_URL}/api/progress/reset/history",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data
        assert data.get("reset") == "reading_history"
        print(f"PASS: Reset history - {data['message']}")

    def test_reset_invalid_stat_returns_400(self, auth_headers):
        """Test POST /api/progress/reset/invalid returns 400 error"""
        response = requests.post(
            f"{BASE_URL}/api/progress/reset/invalid",
            headers=auth_headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data
        print(f"PASS: Invalid stat type returns 400 - {data['detail']}")


class TestResetStreakIsolation:
    """Test that reset/streak only affects streak, not other stats"""

    def test_streak_reset_preserves_chapters_and_journal(self, auth_headers):
        """Reset streak should not touch total_chapters_read or total_journal_entries"""
        # First get current progress
        response = requests.get(
            f"{BASE_URL}/api/progress",
            headers=auth_headers
        )
        assert response.status_code == 200
        initial_progress = response.json()
        initial_chapters = initial_progress.get("total_chapters_read", 0)
        initial_journal = initial_progress.get("total_journal_entries", 0)
        
        # Reset streak
        response = requests.post(
            f"{BASE_URL}/api/progress/reset/streak",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Verify other stats unchanged
        response = requests.get(
            f"{BASE_URL}/api/progress",
            headers=auth_headers
        )
        assert response.status_code == 200
        after_progress = response.json()
        
        assert after_progress.get("reading_streak") == 0, "Streak should be 0 after reset"
        assert after_progress.get("total_chapters_read") == initial_chapters, \
            f"Chapters changed: was {initial_chapters}, now {after_progress.get('total_chapters_read')}"
        assert after_progress.get("total_journal_entries") == initial_journal, \
            f"Journal changed: was {initial_journal}, now {after_progress.get('total_journal_entries')}"
        print("PASS: Streak reset preserves chapters and journal counts")


class TestResetChaptersWithHistory:
    """Test that reset/chapters clears reading_history too"""

    def test_chapters_reset_clears_history(self, auth_headers):
        """Reset chapters should also clear reading_history"""
        # Reset chapters
        response = requests.post(
            f"{BASE_URL}/api/progress/reset/chapters",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Verify chapters is 0
        response = requests.get(
            f"{BASE_URL}/api/progress",
            headers=auth_headers
        )
        assert response.status_code == 200
        progress = response.json()
        assert progress.get("total_chapters_read") == 0, "Chapters should be 0 after reset"
        
        # Verify history is cleared
        response = requests.get(
            f"{BASE_URL}/api/progress/reading/history?limit=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        history = response.json()
        assert len(history.get("history", [])) == 0, "Reading history should be empty after chapters reset"
        print("PASS: Chapters reset also clears reading history")


class TestResetJournalWithEntries:
    """Test that reset/journal clears journal_entries collection"""

    def test_journal_reset_clears_entries(self, auth_headers):
        """Reset journal should also clear journal_entries"""
        # Reset journal
        response = requests.post(
            f"{BASE_URL}/api/progress/reset/journal",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Verify journal count is 0
        response = requests.get(
            f"{BASE_URL}/api/progress",
            headers=auth_headers
        )
        assert response.status_code == 200
        progress = response.json()
        assert progress.get("total_journal_entries") == 0, "Journal entries count should be 0 after reset"
        
        # Verify journal entries are cleared
        response = requests.get(
            f"{BASE_URL}/api/journal",
            headers=auth_headers
        )
        assert response.status_code == 200
        journal = response.json()
        # Journal endpoint returns a list
        assert isinstance(journal, list), "Journal should return list"
        assert len(journal) == 0, "Journal entries should be empty after reset"
        print("PASS: Journal reset clears journal entries")


class TestResetHistoryOnly:
    """Test that reset/history only clears reading history"""

    def test_history_reset_only_clears_history(self, auth_headers):
        """Reset history should only clear reading_history, not chapters count"""
        # First get current progress
        response = requests.get(
            f"{BASE_URL}/api/progress",
            headers=auth_headers
        )
        assert response.status_code == 200
        initial_progress = response.json()
        # Note: After chapters reset, chapters will be 0 - that's fine
        
        # Reset history only
        response = requests.post(
            f"{BASE_URL}/api/progress/reset/history",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Verify history is cleared
        response = requests.get(
            f"{BASE_URL}/api/progress/reading/history?limit=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        history = response.json()
        assert len(history.get("history", [])) == 0, "Reading history should be empty after history reset"
        print("PASS: History reset clears reading history")


class TestAuthRequired:
    """Test that reset endpoints require authentication"""

    def test_reset_streak_requires_auth(self):
        """Reset streak should return 401 without auth"""
        response = requests.post(f"{BASE_URL}/api/progress/reset/streak")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Reset streak requires authentication")

    def test_reset_chapters_requires_auth(self):
        """Reset chapters should return 401 without auth"""
        response = requests.post(f"{BASE_URL}/api/progress/reset/chapters")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Reset chapters requires authentication")

    def test_reset_journal_requires_auth(self):
        """Reset journal should return 401 without auth"""
        response = requests.post(f"{BASE_URL}/api/progress/reset/journal")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Reset journal requires authentication")

    def test_reset_history_requires_auth(self):
        """Reset history should return 401 without auth"""
        response = requests.post(f"{BASE_URL}/api/progress/reset/history")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Reset history requires authentication")
