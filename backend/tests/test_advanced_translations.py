"""
Test advanced quiz subcategory translations for iteration 33
Tests:
1. Advanced subcategory quiz returns Italian questions for lang=it
2. Advanced subcategory quiz returns English translated questions for lang=en
3. Advanced subcategory quiz returns Spanish translated questions for lang=es
4. Advanced subcategory quiz returns German translated questions for lang=de
5. Advanced subcategory quiz returns French translated questions for lang=fr
6. Advanced subcategory quiz returns Portuguese translated questions for lang=pt
7. All 6 subcategories have translations for all 5 non-Italian languages
8. Quiz submit works with advanced subcategory topics (adv_ prefix)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://bible-quiz-themed.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "testbible@cibospirituale.it"
TEST_PASSWORD = "Test123!"

# All 6 advanced subcategory IDs
SUBCATEGORY_IDS = [
    "adv_critica_testuale",
    "adv_esegesi_biblica", 
    "adv_lingue_bibliche",
    "adv_teologia_nt",
    "adv_teologia_at",
    "adv_storia_chiesa"
]

# Supported languages for translations (excluding Italian which is the source)
TRANSLATION_LANGUAGES = ["en", "es", "de", "fr", "pt"]


@pytest.fixture(scope="module")
def auth_token():
    """Login and get session token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("session_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    return None


class TestAdvancedQuizItalian:
    """Test that Italian questions are returned for lang=it"""

    def test_critica_testuale_italian(self):
        """Test Critica Testuale returns Italian questions"""
        response = requests.get(f"{BASE_URL}/api/quiz/advanced-subcategory/adv_critica_testuale?lang=it")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "questions" in data
        assert len(data["questions"]) == 8, f"Expected 8 questions, got {len(data['questions'])}"
        # Check first question is in Italian (contains Italian-specific text patterns)
        q1 = data["questions"][0]
        assert "question" in q1
        assert "Nella critica testuale" in q1["question"] or "Omeoteluto" in q1["question"] or "indica" in q1["question"]
        print(f"PASSED: Critica Testuale returns {len(data['questions'])} Italian questions")

    def test_all_subcategories_return_8_questions_italian(self):
        """Test all 6 subcategories return 8 questions each in Italian"""
        for sub_id in SUBCATEGORY_IDS:
            response = requests.get(f"{BASE_URL}/api/quiz/advanced-subcategory/{sub_id}?lang=it")
            assert response.status_code == 200, f"Failed for {sub_id}: {response.text}"
            data = response.json()
            assert len(data["questions"]) == 8, f"{sub_id}: Expected 8, got {len(data['questions'])}"
        print(f"PASSED: All 6 subcategories return 8 questions each in Italian")


class TestAdvancedQuizEnglish:
    """Test English translations for advanced subcategories"""

    def test_critica_testuale_english(self):
        """Test Critica Testuale returns English translated questions"""
        response = requests.get(f"{BASE_URL}/api/quiz/advanced-subcategory/adv_critica_testuale?lang=en")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert len(data["questions"]) == 8
        q1 = data["questions"][0]
        # Should contain English text
        assert "textual criticism" in q1["question"].lower() or "homoioteleuton" in q1["question"].lower() or "indicates" in q1["question"].lower()
        print(f"PASSED: Critica Testuale returns English questions")

    def test_esegesi_english(self):
        """Test Esegesi Biblica returns English translated questions"""
        response = requests.get(f"{BASE_URL}/api/quiz/advanced-subcategory/adv_esegesi_biblica?lang=en")
        assert response.status_code == 200
        data = response.json()
        assert len(data["questions"]) == 8
        q1 = data["questions"][0]
        # Check English content
        assert "exegesis" in q1["question"].lower() or "inclusio" in q1["question"].lower() or "rhetorical" in q1["question"].lower()
        print(f"PASSED: Esegesi Biblica returns English questions")


class TestAdvancedQuizSpanish:
    """Test Spanish translations for advanced subcategories"""

    def test_critica_testuale_spanish(self):
        """Test Critica Testuale returns Spanish translated questions"""
        response = requests.get(f"{BASE_URL}/api/quiz/advanced-subcategory/adv_critica_testuale?lang=es")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert len(data["questions"]) == 8
        q1 = data["questions"][0]
        # Should contain Spanish text patterns
        assert "crítica" in q1["question"].lower() or "textual" in q1["question"].lower() or "indica" in q1["question"].lower()
        print(f"PASSED: Critica Testuale returns Spanish questions")

    def test_lingue_bibliche_spanish(self):
        """Test Lingue Bibliche returns Spanish translated questions"""
        response = requests.get(f"{BASE_URL}/api/quiz/advanced-subcategory/adv_lingue_bibliche?lang=es")
        assert response.status_code == 200
        data = response.json()
        assert len(data["questions"]) == 8
        print(f"PASSED: Lingue Bibliche returns Spanish questions")


class TestAdvancedQuizGerman:
    """Test German translations for advanced subcategories"""

    def test_critica_testuale_german(self):
        """Test Critica Testuale returns German translated questions"""
        response = requests.get(f"{BASE_URL}/api/quiz/advanced-subcategory/adv_critica_testuale?lang=de")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert len(data["questions"]) == 8
        q1 = data["questions"][0]
        # Should contain German text patterns
        assert "Textkritik" in q1["question"] or "Phänomen" in q1["question"] or "bezeichnet" in q1["question"] or "Bereich" in q1["question"]
        print(f"PASSED: Critica Testuale returns German questions")

    def test_teologia_nt_german(self):
        """Test Teologia NT returns German translated questions"""
        response = requests.get(f"{BASE_URL}/api/quiz/advanced-subcategory/adv_teologia_nt?lang=de")
        assert response.status_code == 200
        data = response.json()
        assert len(data["questions"]) == 8
        print(f"PASSED: Teologia NT returns German questions")


class TestAdvancedQuizFrench:
    """Test French translations for advanced subcategories"""

    def test_critica_testuale_french(self):
        """Test Critica Testuale returns French translated questions"""
        response = requests.get(f"{BASE_URL}/api/quiz/advanced-subcategory/adv_critica_testuale?lang=fr")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert len(data["questions"]) == 8
        q1 = data["questions"][0]
        # Should contain French text patterns
        assert "critique textuelle" in q1["question"].lower() or "phénomène" in q1["question"].lower() or "indique" in q1["question"].lower()
        print(f"PASSED: Critica Testuale returns French questions")


class TestAdvancedQuizPortuguese:
    """Test Portuguese translations for advanced subcategories"""

    def test_critica_testuale_portuguese(self):
        """Test Critica Testuale returns Portuguese translated questions"""
        response = requests.get(f"{BASE_URL}/api/quiz/advanced-subcategory/adv_critica_testuale?lang=pt")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert len(data["questions"]) == 8
        q1 = data["questions"][0]
        # Should contain Portuguese text patterns
        assert "crítica textual" in q1["question"].lower() or "fenômeno" in q1["question"].lower() or "indica" in q1["question"].lower()
        print(f"PASSED: Critica Testuale returns Portuguese questions")


class TestAllSubcategoriesAllLanguages:
    """Comprehensive test: All 6 subcategories in all 5 translated languages"""

    def test_all_translations_exist(self):
        """Test all 6 subcategories have translations for all 5 languages"""
        missing = []
        for sub_id in SUBCATEGORY_IDS:
            for lang in TRANSLATION_LANGUAGES:
                response = requests.get(f"{BASE_URL}/api/quiz/advanced-subcategory/{sub_id}?lang={lang}")
                if response.status_code != 200:
                    missing.append(f"{sub_id}:{lang}")
                    continue
                data = response.json()
                if len(data.get("questions", [])) != 8:
                    missing.append(f"{sub_id}:{lang} (only {len(data.get('questions', []))} questions)")
        
        assert len(missing) == 0, f"Missing translations: {missing}"
        print(f"PASSED: All 6 subcategories × 5 languages = 30 translation sets verified")


class TestQuizSubmitAdvanced:
    """Test quiz submission with adv_ prefixed topics"""

    def test_submit_quiz_requires_auth(self):
        """Test quiz submit without auth returns 401"""
        response = requests.post(f"{BASE_URL}/api/quiz/submit", json={
            "topic": "adv_critica_testuale",
            "answers": {"ct_1": 1, "ct_2": 2},
            "lang": "it"
        })
        assert response.status_code == 401 or response.status_code == 403
        print(f"PASSED: Quiz submit requires authentication")

    def test_submit_advanced_quiz(self, auth_token):
        """Test submitting an advanced quiz with authentication"""
        if not auth_token:
            pytest.skip("No auth token available")
        
        # First get quiz questions
        response = requests.get(f"{BASE_URL}/api/quiz/advanced-subcategory/adv_critica_testuale?lang=it")
        assert response.status_code == 200
        quiz_data = response.json()
        
        # Create answers dict with all correct answers
        answers = {}
        for q in quiz_data["questions"]:
            answers[q["id"]] = q["correct"]
        
        # Submit quiz
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/quiz/submit",
            json={
                "topic": "adv_critica_testuale",
                "answers": answers,
                "lang": "it"
            },
            headers=headers
        )
        assert response.status_code == 200, f"Submit failed: {response.text}"
        result = response.json()
        assert "score" in result
        assert result["score"] == 100  # All correct answers
        print(f"PASSED: Advanced quiz submit works - score: {result['score']}%")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
