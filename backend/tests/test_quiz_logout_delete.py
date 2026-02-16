"""
Test suite for Quiz multilingual support (10+ quizzes per language) and Auth endpoints
Tests:
1. Quiz topics API returns 10+ quizzes for all 6 languages
2. Quiz titles are translated in each language
3. Delete account endpoint requires authentication
4. Logout endpoint works correctly
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://settings-bugs-fix.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "testbible@cibospirituale.it"
TEST_PASSWORD = "Test123!"


class TestQuizMultilingual:
    """Quiz API tests - verify 10+ quizzes per language with translations"""
    
    @pytest.mark.parametrize("lang,min_count", [
        ("it", 10),  # Italian should have 10+ quizzes
        ("es", 10),  # Spanish should have 10+ quizzes
        ("en", 10),  # English should have 10+ quizzes
        ("de", 10),  # German should have 10+ quizzes
        ("fr", 10),  # French should have 10+ quizzes
        ("pt", 10),  # Portuguese should have 10+ quizzes
    ])
    def test_quiz_topics_count_per_language(self, lang, min_count):
        """Each language should have at least 10 quiz topics"""
        response = requests.get(f"{BASE_URL}/api/quiz/topics?lang={lang}")
        assert response.status_code == 200, f"Failed for {lang}: {response.text}"
        
        topics = response.json()
        assert isinstance(topics, list), f"Expected list for {lang}"
        assert len(topics) >= min_count, f"{lang} has only {len(topics)} quizzes, expected {min_count}+"
        
        # Verify each topic has required fields
        for topic in topics:
            assert "id" in topic, f"Missing 'id' in topic for {lang}"
            assert "title" in topic, f"Missing 'title' in topic for {lang}"
    
    def test_quiz_titles_translated_spanish(self):
        """Spanish quiz titles should be in Spanish"""
        response = requests.get(f"{BASE_URL}/api/quiz/topics?lang=es")
        assert response.status_code == 200
        
        topics = response.json()
        # Find genesis quiz
        genesis_topic = next((t for t in topics if t.get("id") == "genesis"), None)
        assert genesis_topic is not None, "Genesis quiz not found in Spanish"
        assert "Quiz de Génesis" in genesis_topic.get("title", ""), f"Spanish title not translated: {genesis_topic.get('title')}"
    
    def test_quiz_titles_translated_english(self):
        """English quiz titles should be in English"""
        response = requests.get(f"{BASE_URL}/api/quiz/topics?lang=en")
        assert response.status_code == 200
        
        topics = response.json()
        # Find genesis quiz
        genesis_topic = next((t for t in topics if t.get("id") == "genesis"), None)
        assert genesis_topic is not None, "Genesis quiz not found in English"
        assert "Genesis Quiz" in genesis_topic.get("title", ""), f"English title not translated: {genesis_topic.get('title')}"
    
    def test_quiz_titles_translated_german(self):
        """German quiz titles should be in German"""
        response = requests.get(f"{BASE_URL}/api/quiz/topics?lang=de")
        assert response.status_code == 200
        
        topics = response.json()
        # Find genesis quiz
        genesis_topic = next((t for t in topics if t.get("id") == "genesis"), None)
        assert genesis_topic is not None, "Genesis quiz not found in German"
        assert "Genesis Quiz" in genesis_topic.get("title", "") or "Quiz" in genesis_topic.get("title", ""), f"German title: {genesis_topic.get('title')}"
    
    def test_quiz_titles_translated_french(self):
        """French quiz titles should be in French"""
        response = requests.get(f"{BASE_URL}/api/quiz/topics?lang=fr")
        assert response.status_code == 200
        
        topics = response.json()
        # Find genesis quiz
        genesis_topic = next((t for t in topics if t.get("id") == "genese"), None)
        assert genesis_topic is not None, "Genesis quiz not found in French"
        assert "Quiz" in genesis_topic.get("title", ""), f"French title: {genesis_topic.get('title')}"
    
    def test_quiz_titles_translated_portuguese(self):
        """Portuguese quiz titles should be in Portuguese"""
        response = requests.get(f"{BASE_URL}/api/quiz/topics?lang=pt")
        assert response.status_code == 200
        
        topics = response.json()
        # Find genesis quiz
        genesis_topic = next((t for t in topics if t.get("id") == "genesis"), None)
        assert genesis_topic is not None, "Genesis quiz not found in Portuguese"
        assert "Quiz" in genesis_topic.get("title", ""), f"Portuguese title: {genesis_topic.get('title')}"
    
    def test_quiz_questions_translated_english(self):
        """English quiz questions should be in English"""
        response = requests.get(f"{BASE_URL}/api/quiz/genesis?lang=en")
        assert response.status_code == 200
        
        quiz = response.json()
        assert "questions" in quiz, "Missing questions in quiz"
        assert len(quiz["questions"]) > 0, "No questions in quiz"
        
        # Check first question is in English
        first_q = quiz["questions"][0]
        assert "question" in first_q, "Missing question text"
        # English questions should contain English words
        question_text = first_q["question"].lower()
        assert any(word in question_text for word in ["what", "who", "how", "which", "where", "when"]), \
            f"Question doesn't appear to be in English: {first_q['question']}"


class TestAuthEndpoints:
    """Authentication endpoint tests"""
    
    def test_delete_account_requires_auth(self):
        """Delete account endpoint should require authentication"""
        response = requests.delete(f"{BASE_URL}/api/auth/delete-account")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data, "Missing error detail"
    
    def test_login_success(self):
        """Login with valid credentials should succeed"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        
        # If user doesn't exist, register first
        if response.status_code == 401:
            # Try to register
            reg_response = requests.post(
                f"{BASE_URL}/api/auth/register",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "name": "Test User"},
                headers={"Content-Type": "application/json"}
            )
            if reg_response.status_code in [200, 201]:
                response = requests.post(
                    f"{BASE_URL}/api/auth/login",
                    json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
                    headers={"Content-Type": "application/json"}
                )
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "session_token" in data, "Missing session_token"
        assert "user" in data, "Missing user data"
        return data["session_token"]
    
    def test_logout_with_token(self):
        """Logout should work with valid token"""
        # First login
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code != 200:
            pytest.skip("Could not login to test logout")
        
        token = login_response.json().get("session_token")
        
        # Now logout
        logout_response = requests.post(
            f"{BASE_URL}/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert logout_response.status_code == 200, f"Logout failed: {logout_response.text}"
    
    def test_me_endpoint_with_token(self):
        """Me endpoint should return user data with valid token"""
        # First login
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code != 200:
            pytest.skip("Could not login to test /me endpoint")
        
        token = login_response.json().get("session_token")
        
        # Get user info
        me_response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert me_response.status_code == 200, f"Me endpoint failed: {me_response.text}"
        
        user = me_response.json()
        assert "email" in user, "Missing email in user data"
        assert user["email"] == TEST_EMAIL, f"Email mismatch: {user['email']}"


class TestQuizTopicDetails:
    """Detailed quiz topic tests"""
    
    def test_all_languages_have_genesis_quiz(self):
        """All languages should have a Genesis quiz"""
        genesis_ids = {
            "it": "genesi",
            "es": "genesis",
            "en": "genesis",
            "de": "genesis",
            "fr": "genese",
            "pt": "genesis"
        }
        
        for lang, expected_id in genesis_ids.items():
            response = requests.get(f"{BASE_URL}/api/quiz/topics?lang={lang}")
            assert response.status_code == 200, f"Failed for {lang}"
            
            topics = response.json()
            topic_ids = [t.get("id") for t in topics]
            assert expected_id in topic_ids, f"Genesis quiz ({expected_id}) not found in {lang}: {topic_ids}"
    
    def test_all_languages_have_psalms_quiz(self):
        """All languages should have a Psalms quiz"""
        psalms_ids = {
            "it": "salmi",
            "es": "salmos",
            "en": "psalms",
            "de": "psalmen",
            "fr": "psaumes",
            "pt": "salmos"
        }
        
        for lang, expected_id in psalms_ids.items():
            response = requests.get(f"{BASE_URL}/api/quiz/topics?lang={lang}")
            assert response.status_code == 200, f"Failed for {lang}"
            
            topics = response.json()
            topic_ids = [t.get("id") for t in topics]
            assert expected_id in topic_ids, f"Psalms quiz ({expected_id}) not found in {lang}: {topic_ids}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
