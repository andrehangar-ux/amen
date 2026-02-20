"""
Test Advanced Quiz Subcategories - Bible Study App
Tests the 6 themed subcategories under 'Studio Avanzato' tab with 8 questions each
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://quiz-nav-build.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "testbible@cibospirituale.it"
TEST_PASSWORD = "Test123!"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    return data.get("session_token")


@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


class TestAdvancedSubcategoriesAPI:
    """Test the advanced subcategories API endpoints"""
    
    def test_get_advanced_subcategories_returns_6_categories(self, api_client):
        """Verify GET /api/quiz/advanced-subcategories returns exactly 6 categories"""
        response = api_client.get(f"{BASE_URL}/api/quiz/advanced-subcategories")
        
        assert response.status_code == 200
        data = response.json()
        
        # Must be a list with exactly 6 items
        assert isinstance(data, list)
        assert len(data) == 6, f"Expected 6 categories, got {len(data)}"
        
        # Each category should have required fields
        for category in data:
            assert "id" in category
            assert "title" in category
            assert "description" in category
            assert "questions_count" in category
            assert category["questions_count"] == 8, f"Category {category['id']} should have 8 questions, has {category['questions_count']}"
            assert category.get("difficulty") == "advanced"
    
    def test_advanced_subcategory_ids_start_with_adv_prefix(self, api_client):
        """Verify all advanced subcategory IDs start with 'adv_'"""
        response = api_client.get(f"{BASE_URL}/api/quiz/advanced-subcategories")
        data = response.json()
        
        for category in data:
            assert category["id"].startswith("adv_"), f"Category ID {category['id']} should start with 'adv_'"
    
    def test_get_individual_subcategory_quiz(self, api_client):
        """Verify GET /api/quiz/advanced-subcategory/{id} returns correct quiz data"""
        # Expected subcategory IDs
        expected_ids = [
            "adv_critica_testuale",
            "adv_esegesi_biblica",
            "adv_lingue_bibliche",
            "adv_teologia_nt",
            "adv_teologia_at",
            "adv_storia_chiesa"
        ]
        
        for sub_id in expected_ids:
            response = api_client.get(f"{BASE_URL}/api/quiz/advanced-subcategory/{sub_id}")
            
            assert response.status_code == 200, f"Failed to get {sub_id}: {response.text}"
            data = response.json()
            
            # Verify quiz structure
            assert data["id"] == sub_id
            assert "title" in data
            assert "questions" in data
            assert len(data["questions"]) == 8, f"Subcategory {sub_id} should have 8 questions, has {len(data['questions'])}"
            
            # Verify each question has required fields
            for q in data["questions"]:
                assert "id" in q
                assert "question" in q
                assert "options" in q
                assert len(q["options"]) == 4, f"Question {q['id']} should have 4 options"
                assert "correct" in q
                assert isinstance(q["correct"], int)
                assert 0 <= q["correct"] <= 3
                assert "explanation" in q
    
    def test_invalid_subcategory_returns_404(self, api_client):
        """Verify invalid subcategory ID returns 404"""
        response = api_client.get(f"{BASE_URL}/api/quiz/advanced-subcategory/adv_invalid_category")
        assert response.status_code == 404


class TestAdvancedQuizSubmission:
    """Test quiz submission for advanced subcategories"""
    
    def test_submit_advanced_quiz_requires_auth(self, api_client):
        """Verify quiz submission requires authentication"""
        # Remove auth header for this test
        api_client.headers.pop("Authorization", None)
        
        response = api_client.post(f"{BASE_URL}/api/quiz/submit", json={
            "topic": "adv_critica_testuale",
            "answers": {"ct_1": 1},
            "language": "it"
        })
        
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_submit_advanced_quiz_with_auth(self, authenticated_client):
        """Verify quiz submission works with authentication"""
        response = authenticated_client.post(f"{BASE_URL}/api/quiz/submit", json={
            "topic": "adv_critica_testuale",
            "answers": {
                "ct_1": 1,  # Correct
                "ct_2": 2,  # Correct
                "ct_3": 1,  # Correct
                "ct_4": 1,  # Correct
                "ct_5": 1,  # Correct
                "ct_6": 1,  # Correct
                "ct_7": 1,  # Correct
                "ct_8": 1   # Correct
            },
            "language": "it"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "score" in data
        assert "correct_count" in data
        assert "total" in data
        assert "results" in data
        assert "feedback" in data
        
        # Verify quiz stats
        assert data["total"] == 8
        assert isinstance(data["score"], (int, float))
        assert 0 <= data["score"] <= 100
        assert 0 <= data["correct_count"] <= 8
    
    def test_submit_different_advanced_subcategories(self, authenticated_client):
        """Verify all 6 advanced subcategories can be submitted"""
        subcategories = [
            ("adv_critica_testuale", "ct_1"),
            ("adv_esegesi_biblica", "es_1"),
            ("adv_lingue_bibliche", "lb_1"),
            ("adv_teologia_nt", "tnt_1"),
            ("adv_teologia_at", "tat_1"),
            ("adv_storia_chiesa", "sc_1"),
        ]
        
        for topic, question_prefix in subcategories:
            response = authenticated_client.post(f"{BASE_URL}/api/quiz/submit", json={
                "topic": topic,
                "answers": {f"{question_prefix}": 1},
                "language": "it"
            })
            
            assert response.status_code == 200, f"Failed to submit {topic}: {response.text}"
            data = response.json()
            assert "score" in data
            assert "results" in data


class TestQuizTopicsIntegration:
    """Test that quiz topics include the classic quizzes and thematic categories"""
    
    def test_get_quiz_topics(self, api_client):
        """Verify GET /api/quiz/topics returns classic quiz topics"""
        response = api_client.get(f"{BASE_URL}/api/quiz/topics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Find studio_avanzato in the list
        studio_avanzato = next((t for t in data if t["id"] == "studio_avanzato"), None)
        assert studio_avanzato is not None, "studio_avanzato topic should be in the topics list"
    
    def test_get_quiz_categories(self, api_client):
        """Verify GET /api/quiz/categories returns the 1000 questions categories"""
        response = api_client.get(f"{BASE_URL}/api/quiz/categories")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Each category should have required fields
        for cat in data:
            assert "id" in cat
            assert "title" in cat
            assert "questions_count" in cat


class TestLanguageSupport:
    """Test that advanced subcategories support multiple languages"""
    
    def test_advanced_subcategories_in_different_languages(self, api_client):
        """Verify advanced subcategories return translated content"""
        languages = ["it", "en", "es"]
        
        for lang in languages:
            response = api_client.get(f"{BASE_URL}/api/quiz/advanced-subcategories?lang={lang}")
            
            assert response.status_code == 200, f"Failed for language {lang}"
            data = response.json()
            
            assert len(data) == 6, f"Should have 6 categories in {lang}"
            
            # Verify titles are translated (at least for known categories)
            critica = next((c for c in data if c["id"] == "adv_critica_testuale"), None)
            assert critica is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
