"""
Backend tests for Quiz Translation and Submit features
Tests:
- Quiz categories endpoint with different languages
- Quiz category questions translation on-demand
- Quiz submit endpoint with statistics calculation
- Results structure validation (wrongAnswers, correctAnswers)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://spirit-study-update.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "testbible@cibospirituale.it"
TEST_PASSWORD = "Test123!"


class TestQuizCategories:
    """Test quiz categories listing with translations"""
    
    def test_get_categories_italian(self):
        """Test getting categories in Italian (default)"""
        response = requests.get(f"{BASE_URL}/api/quiz/categories?lang=it")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 33  # 33 categories
        
        # Verify Italian titles
        titles = [c['title'] for c in data]
        assert 'La Creazione' in titles
        assert 'Abramo' in titles
        
    def test_get_categories_english(self):
        """Test getting categories in English"""
        response = requests.get(f"{BASE_URL}/api/quiz/categories?lang=en")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 33
        
        # Verify English titles
        titles = [c['title'] for c in data]
        assert 'The Creation' in titles
        assert 'Abraham' in titles
        
    def test_get_categories_spanish(self):
        """Test getting categories in Spanish"""
        response = requests.get(f"{BASE_URL}/api/quiz/categories?lang=es")
        assert response.status_code == 200
        
        data = response.json()
        titles = [c['title'] for c in data]
        assert 'La Creación' in titles
        assert 'Abraham' in titles
        
    def test_get_categories_german(self):
        """Test getting categories in German"""
        response = requests.get(f"{BASE_URL}/api/quiz/categories?lang=de")
        assert response.status_code == 200
        
        data = response.json()
        titles = [c['title'] for c in data]
        assert 'Die Schöpfung' in titles
        assert 'Abraham' in titles
        
    def test_get_categories_french(self):
        """Test getting categories in French"""
        response = requests.get(f"{BASE_URL}/api/quiz/categories?lang=fr")
        assert response.status_code == 200
        
        data = response.json()
        titles = [c['title'] for c in data]
        assert 'La Création' in titles
        assert 'Abraham' in titles
        
    def test_get_categories_portuguese(self):
        """Test getting categories in Portuguese"""
        response = requests.get(f"{BASE_URL}/api/quiz/categories?lang=pt")
        assert response.status_code == 200
        
        data = response.json()
        titles = [c['title'] for c in data]
        assert 'A Criação' in titles
        assert 'Abraão' in titles


class TestQuizCategoryQuestions:
    """Test quiz questions retrieval by category with translation"""
    
    def test_get_category_quiz_italian(self):
        """Test getting quiz questions in Italian"""
        response = requests.get(f"{BASE_URL}/api/quiz/category/cat_creazione?lang=it")
        assert response.status_code == 200
        
        data = response.json()
        assert 'questions' in data
        assert len(data['questions']) == 30  # Limit 30 per session
        assert data['title'] == 'La Creazione'
        
        # Verify question structure
        q = data['questions'][0]
        assert 'id' in q
        assert 'question' in q
        assert 'options' in q
        assert len(q['options']) == 4
        assert 'correct' in q
        assert 'explanation' in q
        
    def test_get_category_quiz_english_translation(self):
        """Test questions are translated to English"""
        response = requests.get(f"{BASE_URL}/api/quiz/category/cat_creazione?lang=en")
        assert response.status_code == 200
        
        data = response.json()
        assert data['title'] == 'The Creation'
        assert len(data['questions']) == 30
        
        # First question should be in English (translated)
        q = data['questions'][0]
        # Question text should contain English words
        assert 'Adam' in q['question'] or 'mean' in q['question'] or 'What' in q['question']
        
    def test_invalid_category(self):
        """Test invalid category returns 404"""
        response = requests.get(f"{BASE_URL}/api/quiz/category/invalid_category?lang=it")
        assert response.status_code == 404


class TestQuizSubmit:
    """Test quiz submission and statistics"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("session_token")
        pytest.skip("Authentication failed")
    
    def test_submit_quiz_returns_statistics(self, auth_token):
        """Test quiz submission returns proper statistics"""
        # Get quiz questions first
        quiz_response = requests.get(f"{BASE_URL}/api/quiz/category/cat_creazione?lang=it")
        assert quiz_response.status_code == 200
        questions = quiz_response.json()['questions']
        
        # Create answers dict - answer some correctly
        answers = {}
        for q in questions:
            # Answer first question correctly, others incorrectly
            answers[q['id']] = q['correct'] if q == questions[0] else (q['correct'] + 1) % 4
        
        response = requests.post(
            f"{BASE_URL}/api/quiz/submit",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "topic": "cat_creazione",
                "answers": answers,
                "language": "it"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert 'score' in data
        assert 'correct_count' in data
        assert 'total' in data
        assert 'results' in data
        assert 'feedback' in data
        
        # Verify data values
        assert data['total'] == 30
        assert data['correct_count'] >= 0
        assert 0 <= data['score'] <= 100
        
    def test_submit_quiz_results_structure(self, auth_token):
        """Test that results contain proper structure for UI display"""
        # Get questions
        quiz_response = requests.get(f"{BASE_URL}/api/quiz/category/cat_patriarchi_2?lang=it")
        questions = quiz_response.json()['questions']
        
        # All wrong answers
        answers = {q['id']: (q['correct'] + 1) % 4 for q in questions}
        
        response = requests.post(
            f"{BASE_URL}/api/quiz/submit",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "topic": "cat_patriarchi_2",
                "answers": answers,
                "language": "it"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check results structure
        assert len(data['results']) == 30
        
        for result in data['results']:
            assert 'question_id' in result
            assert 'is_correct' in result
            assert 'correct_answer' in result
            assert 'user_answer' in result
            assert 'explanation' in result
            assert 'verse_ref' in result
            
    def test_submit_quiz_feedback_language(self, auth_token):
        """Test feedback is in correct language"""
        quiz_response = requests.get(f"{BASE_URL}/api/quiz/category/cat_creazione?lang=it")
        questions = quiz_response.json()['questions']
        
        # Some correct answers
        answers = {q['id']: q['correct'] for i, q in enumerate(questions) if i < 10}
        for i, q in enumerate(questions):
            if i >= 10:
                answers[q['id']] = (q['correct'] + 1) % 4
        
        response = requests.post(
            f"{BASE_URL}/api/quiz/submit",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "topic": "cat_creazione",
                "answers": answers,
                "language": "it"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Feedback should be in Italian
        assert data['feedback']
        # Note: Can't strictly verify language but should contain text


class TestQuizTopics:
    """Test classic quiz topics endpoint"""
    
    def test_get_topics_italian(self):
        """Test getting quiz topics in Italian"""
        response = requests.get(f"{BASE_URL}/api/quiz/topics?lang=it")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify topic structure
        for topic in data:
            assert 'id' in topic
            assert 'title' in topic
            assert 'questions_count' in topic


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
