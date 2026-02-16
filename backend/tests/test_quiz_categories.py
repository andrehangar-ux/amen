"""
Test file for Quiz Categories (1000 questions in 33 thematic categories)
Tests the new /api/quiz/categories and /api/quiz/category/{id} endpoints
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://settings-bugs-fix.preview.emergentagent.com').rstrip('/')


class TestQuizCategoriesEndpoints:
    """Tests for the new quiz categories system (1000 questions)"""
    
    def test_get_categories_returns_33_categories(self):
        """Verify that /api/quiz/categories returns 33 categories"""
        response = requests.get(f"{BASE_URL}/api/quiz/categories?lang=it")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 33, f"Expected 33 categories, got {len(data)}"
        
        # Verify each category has required fields
        for category in data:
            assert "id" in category
            assert "title" in category
            assert "description" in category
            assert "questions_count" in category
            assert category["questions_count"] > 0
    
    def test_get_categories_total_1000_questions(self):
        """Verify that total questions across all categories is 1000"""
        response = requests.get(f"{BASE_URL}/api/quiz/categories?lang=it")
        assert response.status_code == 200
        
        data = response.json()
        total_questions = sum(cat["questions_count"] for cat in data)
        assert total_questions == 1000, f"Expected 1000 total questions, got {total_questions}"
    
    def test_get_category_quiz_returns_30_questions(self):
        """Verify that each category quiz returns exactly 30 questions"""
        # First get categories
        categories_response = requests.get(f"{BASE_URL}/api/quiz/categories?lang=it")
        assert categories_response.status_code == 200
        
        categories = categories_response.json()
        # Test first category
        first_category = categories[0]
        
        quiz_response = requests.get(f"{BASE_URL}/api/quiz/category/{first_category['id']}?lang=it")
        assert quiz_response.status_code == 200
        
        quiz = quiz_response.json()
        assert "questions" in quiz
        assert len(quiz["questions"]) == 30, f"Expected 30 questions, got {len(quiz['questions'])}"
        
        # Verify question structure
        for question in quiz["questions"]:
            assert "id" in question
            assert "question" in question
            assert "options" in question
            assert len(question["options"]) == 4  # Multiple choice with 4 options
            assert "correct" in question
            assert 0 <= question["correct"] <= 3
    
    def test_categories_translate_titles_in_italian(self):
        """Verify category titles are in Italian when lang=it"""
        response = requests.get(f"{BASE_URL}/api/quiz/categories?lang=it")
        assert response.status_code == 200
        
        data = response.json()
        # Check for known Italian titles
        titles = [cat["title"] for cat in data]
        
        # These should be Italian titles
        italian_titles = ["Abramo", "Apocalisse", "La Creazione", "I Vangeli"]
        found_italian = sum(1 for t in italian_titles if any(t in title for title in titles))
        assert found_italian > 0, "Should have Italian titles when lang=it"
    
    def test_categories_translate_titles_in_english(self):
        """Verify category titles change when switching to English"""
        response_it = requests.get(f"{BASE_URL}/api/quiz/categories?lang=it")
        response_en = requests.get(f"{BASE_URL}/api/quiz/categories?lang=en")
        
        assert response_it.status_code == 200
        assert response_en.status_code == 200
        
        data_it = response_it.json()
        data_en = response_en.json()
        
        # Same number of categories
        assert len(data_it) == len(data_en)
        
        # Check that titles are different (translated)
        titles_it = [cat["title"] for cat in data_it]
        titles_en = [cat["title"] for cat in data_en]
        
        # Find a category that exists in both with different titles
        # Abraham in EN, Abramo in IT
        abraham_in_en = any("Abraham" in t for t in titles_en)
        abramo_in_it = any("Abramo" in t for t in titles_it)
        
        assert abraham_in_en, "Should have 'Abraham' in English titles"
        assert abramo_in_it, "Should have 'Abramo' in Italian titles"
    
    def test_categories_translate_titles_in_spanish(self):
        """Verify category titles change when switching to Spanish"""
        response = requests.get(f"{BASE_URL}/api/quiz/categories?lang=es")
        assert response.status_code == 200
        
        data = response.json()
        titles = [cat["title"] for cat in data]
        
        # Check for Spanish translations
        spanish_titles = ["Abraham", "Apocalipsis", "La Creación"]
        found_spanish = sum(1 for t in spanish_titles if any(t in title for title in titles))
        assert found_spanish > 0, "Should have Spanish titles when lang=es"
    
    def test_categories_translate_titles_in_german(self):
        """Verify category titles change when switching to German"""
        response = requests.get(f"{BASE_URL}/api/quiz/categories?lang=de")
        assert response.status_code == 200
        
        data = response.json()
        titles = [cat["title"] for cat in data]
        
        # Check for German translations
        assert any("Abraham" in t for t in titles) or any("Schöpfung" in t for t in titles), \
            "Should have German titles when lang=de"
    
    def test_categories_translate_titles_in_french(self):
        """Verify category titles change when switching to French"""
        response = requests.get(f"{BASE_URL}/api/quiz/categories?lang=fr")
        assert response.status_code == 200
        
        data = response.json()
        titles = [cat["title"] for cat in data]
        
        # Check for French translations
        french_indicators = ["Création", "Abraham", "Apocalypse"]
        found_french = sum(1 for t in french_indicators if any(t in title for title in titles))
        assert found_french > 0, "Should have French titles when lang=fr"
    
    def test_categories_translate_titles_in_portuguese(self):
        """Verify category titles change when switching to Portuguese"""
        response = requests.get(f"{BASE_URL}/api/quiz/categories?lang=pt")
        assert response.status_code == 200
        
        data = response.json()
        titles = [cat["title"] for cat in data]
        
        # Check for Portuguese translations
        portuguese_indicators = ["Abraão", "A Criação", "Apocalipse"]
        found_portuguese = sum(1 for t in portuguese_indicators if any(t in title for title in titles))
        assert found_portuguese > 0, "Should have Portuguese titles when lang=pt"
    
    def test_get_category_by_id_success(self):
        """Test getting a specific category by ID"""
        response = requests.get(f"{BASE_URL}/api/quiz/category/cat_canone_bibbia?lang=it")
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "title" in data
        assert "questions" in data
        assert len(data["questions"]) == 30
    
    def test_get_category_invalid_id_returns_404(self):
        """Test that invalid category ID returns 404"""
        response = requests.get(f"{BASE_URL}/api/quiz/category/cat_invalid_category?lang=it")
        assert response.status_code == 404
    
    def test_classic_quiz_topics_still_work(self):
        """Verify that classic quiz topics endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/quiz/topics?lang=it")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Classic topics should exist
        assert len(data) > 0


class TestQuizCategoryQuestions:
    """Tests for quiz category question structure and content"""
    
    def test_question_has_explanation(self):
        """Verify each question has an explanation field"""
        response = requests.get(f"{BASE_URL}/api/quiz/category/cat_canone_bibbia?lang=it")
        assert response.status_code == 200
        
        quiz = response.json()
        for question in quiz["questions"]:
            assert "explanation" in question, f"Question {question['id']} missing explanation"
    
    def test_question_options_are_strings(self):
        """Verify question options are all strings"""
        response = requests.get(f"{BASE_URL}/api/quiz/category/cat_creazione?lang=it")
        assert response.status_code == 200
        
        quiz = response.json()
        for question in quiz["questions"]:
            for i, option in enumerate(question["options"]):
                assert isinstance(option, str), f"Question {question['id']} option {i} is not a string"
    
    def test_correct_answer_in_range(self):
        """Verify correct answer index is within options range"""
        response = requests.get(f"{BASE_URL}/api/quiz/category/cat_patriarchi_2?lang=it")
        assert response.status_code == 200
        
        quiz = response.json()
        for question in quiz["questions"]:
            correct = question["correct"]
            options_count = len(question["options"])
            assert 0 <= correct < options_count, \
                f"Question {question['id']} has invalid correct index {correct} for {options_count} options"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
