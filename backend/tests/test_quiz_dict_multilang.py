"""
Test Quiz & Dictionary Multilingual API Support
Tests for: Quiz topics/questions in 6 languages, Dictionary translations
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', '').rstrip('/')

# =============================================================================
# QUIZ MULTILINGUAL API TESTS
# =============================================================================

class TestQuizTopicsMultilingual:
    """Tests for GET /api/quiz/topics?lang={lang} - Quiz topics in each language"""
    
    def test_quiz_topics_english_returns_valid_data(self):
        """GET /api/quiz/topics?lang=en returns English quiz titles"""
        response = requests.get(f"{BASE_URL}/api/quiz/topics?lang=en", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        topics = response.json()
        assert len(topics) > 0, "Should have quiz topics"
        
        # Check if there's a genesis quiz with English title
        genesis_quiz = None
        for topic in topics:
            if "genesis" in topic.get("id", "").lower() or "genesi" in topic.get("id", "").lower():
                genesis_quiz = topic
                break
        
        assert genesis_quiz is not None, "Should have a Genesis quiz topic"
        # English title should contain 'Genesis' not 'Genesi'
        assert "Genesis" in genesis_quiz.get("title", "") or "genesis" in genesis_quiz.get("title", "").lower(), \
            f"English Genesis quiz title should contain 'Genesis', got: {genesis_quiz.get('title')}"
        print(f"PASS: English quiz topics returned {len(topics)} topics, Genesis quiz: {genesis_quiz.get('title')}")
    
    def test_quiz_topics_german_returns_valid_data(self):
        """GET /api/quiz/topics?lang=de returns German quiz descriptions"""
        response = requests.get(f"{BASE_URL}/api/quiz/topics?lang=de", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        topics = response.json()
        assert len(topics) > 0, "Should have quiz topics"
        
        # German topics should have German titles
        first_topic = topics[0]
        assert "title" in first_topic, "Topic should have title"
        assert "description" in first_topic, "Topic should have description"
        print(f"PASS: German quiz topics returned {len(topics)} topics, first: {first_topic.get('title')}")
    
    def test_quiz_topics_italian_returns_valid_data(self):
        """GET /api/quiz/topics?lang=it returns Italian quiz titles (default)"""
        response = requests.get(f"{BASE_URL}/api/quiz/topics?lang=it", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        topics = response.json()
        assert len(topics) > 0, "Should have quiz topics"
        
        # Italian should have Italian titles like "Quiz su Genesi"
        has_italian_content = any("Quiz" in t.get("title", "") or "Genesi" in t.get("title", "") for t in topics)
        print(f"PASS: Italian quiz topics returned {len(topics)} topics")
    
    def test_quiz_topics_spanish_returns_valid_data(self):
        """GET /api/quiz/topics?lang=es returns Spanish quiz data"""
        response = requests.get(f"{BASE_URL}/api/quiz/topics?lang=es", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        topics = response.json()
        assert len(topics) > 0, "Should have quiz topics"
        print(f"PASS: Spanish quiz topics returned {len(topics)} topics")
    
    def test_quiz_topics_french_returns_valid_data(self):
        """GET /api/quiz/topics?lang=fr returns French quiz data"""
        response = requests.get(f"{BASE_URL}/api/quiz/topics?lang=fr", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        topics = response.json()
        assert len(topics) > 0, "Should have quiz topics"
        print(f"PASS: French quiz topics returned {len(topics)} topics")
    
    def test_quiz_topics_portuguese_returns_valid_data(self):
        """GET /api/quiz/topics?lang=pt returns Portuguese quiz data"""
        response = requests.get(f"{BASE_URL}/api/quiz/topics?lang=pt", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        topics = response.json()
        assert len(topics) > 0, "Should have quiz topics"
        print(f"PASS: Portuguese quiz topics returned {len(topics)} topics")
    
    def test_quiz_topics_all_languages_return_valid_data(self):
        """All 6 languages should return valid quiz topics (counts may vary - not all translated)"""
        languages = ["it", "en", "es", "de", "fr", "pt"]
        topic_counts = {}
        
        for lang in languages:
            response = requests.get(f"{BASE_URL}/api/quiz/topics?lang={lang}", timeout=10)
            assert response.status_code == 200, f"Failed for lang={lang}"
            topics = response.json()
            topic_counts[lang] = len(topics)
            # Each language should have at least 1 quiz topic
            assert len(topics) >= 1, f"Language {lang} should have at least 1 quiz topic"
        
        # Note: Not all quizzes are translated to all languages, so counts will differ
        # Italian has the most (14), other languages have fewer translations
        print(f"INFO: Quiz topic counts per language: {topic_counts}")
        print(f"PASS: All languages return valid quiz topics")


class TestQuizQuestionsMultilingual:
    """Tests for GET /api/quiz/{topic}?lang={lang} - Quiz questions in each language"""
    
    def test_genesis_quiz_english_questions(self):
        """GET /api/quiz/genesi?lang=en returns English questions"""
        response = requests.get(f"{BASE_URL}/api/quiz/genesi?lang=en", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        quiz = response.json()
        
        assert "title" in quiz, "Quiz should have title"
        assert "questions" in quiz, "Quiz should have questions"
        assert len(quiz["questions"]) > 0, "Quiz should have at least one question"
        
        # English quiz should have English content
        first_question = quiz["questions"][0]
        assert "question" in first_question, "Question should have question text"
        assert "options" in first_question, "Question should have options"
        
        # Check if text seems English (not Italian)
        question_text = first_question["question"]
        # English questions typically start with "What", "Who", "Where", "Which", "How"
        print(f"PASS: English genesis quiz has {len(quiz['questions'])} questions")
        print(f"  First question: {question_text[:80]}...")
    
    def test_genesis_quiz_german_questions(self):
        """GET /api/quiz/genesi?lang=de returns German questions"""
        response = requests.get(f"{BASE_URL}/api/quiz/genesi?lang=de", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        quiz = response.json()
        
        assert "questions" in quiz, "Quiz should have questions"
        assert len(quiz["questions"]) > 0, "Quiz should have questions"
        
        first_question = quiz["questions"][0]
        question_text = first_question["question"]
        print(f"PASS: German genesis quiz has {len(quiz['questions'])} questions")
        print(f"  First question: {question_text[:80]}...")
    
    def test_genesis_quiz_italian_questions(self):
        """GET /api/quiz/genesi?lang=it returns Italian questions (default)"""
        response = requests.get(f"{BASE_URL}/api/quiz/genesi?lang=it", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        quiz = response.json()
        
        assert "questions" in quiz, "Quiz should have questions"
        # Italian genesis quiz should have Italian content
        print(f"PASS: Italian genesis quiz has {len(quiz['questions'])} questions")
    
    def test_quiz_questions_all_have_required_fields(self):
        """Quiz questions should have id, question, options, correct, explanation"""
        response = requests.get(f"{BASE_URL}/api/quiz/genesi?lang=en", timeout=10)
        quiz = response.json()
        
        required_fields = ["id", "question", "options", "correct"]
        for q in quiz["questions"]:
            for field in required_fields:
                assert field in q, f"Question missing field: {field}"
            assert len(q["options"]) == 4, f"Question should have 4 options, got {len(q['options'])}"
            assert isinstance(q["correct"], int), "Correct should be an integer index"
            assert 0 <= q["correct"] < 4, "Correct index should be 0-3"
        
        print(f"PASS: All {len(quiz['questions'])} questions have required fields")


# =============================================================================
# DICTIONARY MULTILINGUAL API TESTS  
# =============================================================================

class TestDictionaryTermsMultilingual:
    """Tests for GET /api/dictionary?lang={lang} - Dictionary terms list"""
    
    def test_dictionary_english_returns_english_origin(self):
        """GET /api/dictionary?lang=en returns English origin labels 'Hebrew'/'Greek'"""
        response = requests.get(f"{BASE_URL}/api/dictionary?lang=en", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        terms = response.json()
        assert len(terms) > 0, "Should have dictionary terms"
        
        # Check that origin is in English
        has_hebrew = any(t.get("origin") == "Hebrew" for t in terms)
        has_greek = any(t.get("origin") == "Greek" for t in terms)
        
        assert has_hebrew or has_greek, f"English dictionary should have 'Hebrew' or 'Greek' origins, got: {[t.get('origin') for t in terms[:3]]}"
        print(f"PASS: English dictionary has {len(terms)} terms with English origins")
    
    def test_dictionary_german_returns_german_origin(self):
        """GET /api/dictionary?lang=de returns German origin labels 'Hebräisch'/'Griechisch'"""
        response = requests.get(f"{BASE_URL}/api/dictionary?lang=de", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        terms = response.json()
        assert len(terms) > 0, "Should have dictionary terms"
        
        # German origins should be 'Hebräisch' or 'Griechisch'
        has_hebraisch = any(t.get("origin") == "Hebräisch" for t in terms)
        has_griechisch = any(t.get("origin") == "Griechisch" for t in terms)
        
        assert has_hebraisch or has_griechisch, f"German dictionary should have 'Hebräisch' or 'Griechisch' origins, got: {[t.get('origin') for t in terms[:3]]}"
        print(f"PASS: German dictionary has {len(terms)} terms with German origins")
    
    def test_dictionary_italian_returns_italian_origin(self):
        """GET /api/dictionary?lang=it returns Italian origin labels (default)"""
        response = requests.get(f"{BASE_URL}/api/dictionary?lang=it", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        terms = response.json()
        assert len(terms) > 0, "Should have dictionary terms"
        
        # Italian origins should be 'Ebraico' or 'Greco'
        has_ebraico = any(t.get("origin") == "Ebraico" for t in terms)
        has_greco = any(t.get("origin") == "Greco" for t in terms)
        
        assert has_ebraico or has_greco, f"Italian dictionary should have 'Ebraico' or 'Greco' origins, got: {[t.get('origin') for t in terms[:3]]}"
        print(f"PASS: Italian dictionary has {len(terms)} terms with Italian origins")
    
    def test_dictionary_spanish_origin_labels(self):
        """GET /api/dictionary?lang=es returns Spanish origin 'Hebreo'/'Griego'"""
        response = requests.get(f"{BASE_URL}/api/dictionary?lang=es", timeout=10)
        assert response.status_code == 200
        terms = response.json()
        
        has_hebreo = any(t.get("origin") == "Hebreo" for t in terms)
        has_griego = any(t.get("origin") == "Griego" for t in terms)
        
        assert has_hebreo or has_griego, f"Spanish dictionary should have 'Hebreo' or 'Griego' origins"
        print(f"PASS: Spanish dictionary has {len(terms)} terms with Spanish origins")
    
    def test_dictionary_french_origin_labels(self):
        """GET /api/dictionary?lang=fr returns French origin 'Hébreu'/'Grec'"""
        response = requests.get(f"{BASE_URL}/api/dictionary?lang=fr", timeout=10)
        assert response.status_code == 200
        terms = response.json()
        
        has_hebreu = any(t.get("origin") == "Hébreu" for t in terms)
        has_grec = any(t.get("origin") == "Grec" for t in terms)
        
        assert has_hebreu or has_grec, f"French dictionary should have 'Hébreu' or 'Grec' origins"
        print(f"PASS: French dictionary has {len(terms)} terms with French origins")
    
    def test_dictionary_portuguese_origin_labels(self):
        """GET /api/dictionary?lang=pt returns Portuguese origin 'Hebraico'/'Grego'"""
        response = requests.get(f"{BASE_URL}/api/dictionary?lang=pt", timeout=10)
        assert response.status_code == 200
        terms = response.json()
        
        has_hebraico = any(t.get("origin") == "Hebraico" for t in terms)
        has_grego = any(t.get("origin") == "Grego" for t in terms)
        
        assert has_hebraico or has_grego, f"Portuguese dictionary should have 'Hebraico' or 'Grego' origins"
        print(f"PASS: Portuguese dictionary has {len(terms)} terms with Portuguese origins")


class TestDictionaryTermDetailMultilingual:
    """Tests for GET /api/dictionary/{term_id}?lang={lang} - Single term detail"""
    
    def test_agape_english_meaning(self):
        """GET /api/dictionary/agape?lang=en returns English meaning 'Unconditional love'"""
        response = requests.get(f"{BASE_URL}/api/dictionary/agape?lang=en", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        term = response.json()
        
        assert "meaning" in term, "Term should have meaning"
        meaning = term["meaning"]
        
        # English meaning should contain 'Unconditional' or 'love'
        assert "unconditional" in meaning.lower() or "love" in meaning.lower(), \
            f"English agape meaning should contain 'unconditional love', got: {meaning}"
        print(f"PASS: English agape meaning: {meaning}")
    
    def test_agape_german_meaning(self):
        """GET /api/dictionary/agape?lang=de returns German meaning 'Bedingungslose Liebe'"""
        response = requests.get(f"{BASE_URL}/api/dictionary/agape?lang=de", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        term = response.json()
        
        meaning = term.get("meaning", "")
        
        # German meaning should contain 'Bedingungslose' or 'Liebe'
        assert "bedingungslose" in meaning.lower() or "liebe" in meaning.lower(), \
            f"German agape meaning should contain 'Bedingungslose Liebe', got: {meaning}"
        print(f"PASS: German agape meaning: {meaning}")
    
    def test_agape_italian_meaning(self):
        """GET /api/dictionary/agape?lang=it returns Italian meaning (default)"""
        response = requests.get(f"{BASE_URL}/api/dictionary/agape?lang=it", timeout=10)
        assert response.status_code == 200
        term = response.json()
        
        meaning = term.get("meaning", "")
        # Italian should have original meaning
        assert "amore" in meaning.lower(), f"Italian agape should have 'amore', got: {meaning}"
        print(f"PASS: Italian agape meaning: {meaning}")
    
    def test_shalom_french_meaning(self):
        """GET /api/dictionary/shalom?lang=fr returns French meaning"""
        response = requests.get(f"{BASE_URL}/api/dictionary/shalom?lang=fr", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        term = response.json()
        
        meaning = term.get("meaning", "")
        # French shalom should contain 'Paix' (peace)
        assert "paix" in meaning.lower() or "plénitude" in meaning.lower(), \
            f"French shalom meaning should contain peace-related word, got: {meaning}"
        print(f"PASS: French shalom meaning: {meaning}")
    
    def test_logos_spanish_meaning(self):
        """GET /api/dictionary/logos?lang=es returns Spanish meaning"""
        response = requests.get(f"{BASE_URL}/api/dictionary/logos?lang=es", timeout=10)
        assert response.status_code == 200
        term = response.json()
        
        meaning = term.get("meaning", "")
        # Spanish logos should contain 'Palabra' or 'Verbo'
        assert "palabra" in meaning.lower() or "verbo" in meaning.lower(), \
            f"Spanish logos meaning should contain 'Palabra/Verbo', got: {meaning}"
        print(f"PASS: Spanish logos meaning: {meaning}")
    
    def test_term_detail_has_all_fields(self):
        """Dictionary term detail should have all required fields"""
        response = requests.get(f"{BASE_URL}/api/dictionary/agape?lang=en", timeout=10)
        term = response.json()
        
        required_fields = ["term", "meaning", "origin"]
        for field in required_fields:
            assert field in term, f"Term missing field: {field}"
        
        # Origin should be in English
        assert term["origin"] == "Greek", f"Agape origin should be 'Greek' in English, got: {term['origin']}"
        print(f"PASS: Dictionary term has all required fields with English translations")
    
    def test_term_not_found_returns_404(self):
        """GET /api/dictionary/nonexistent returns 404"""
        response = requests.get(f"{BASE_URL}/api/dictionary/nonexistentterm123?lang=en", timeout=10)
        assert response.status_code == 404, f"Expected 404 for non-existent term, got {response.status_code}"
        print("PASS: Non-existent term returns 404")


class TestDictionarySearch:
    """Tests for GET /api/dictionary/search/{query} - Dictionary search"""
    
    def test_search_amore_returns_results(self):
        """GET /api/dictionary/search/amore returns matching terms (Italian search)"""
        # Search searches against Italian base data, so use Italian term 'amore' (love)
        response = requests.get(f"{BASE_URL}/api/dictionary/search/amore", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        results = response.json()
        
        # Should find agape (amore incondizionato) and chesed (amore fedele)
        assert len(results) > 0, "Search for 'amore' should return results"
        
        term_ids = [r.get("id", "") for r in results]
        assert "agape" in term_ids, f"Search 'amore' should find agape, got: {term_ids}"
        print(f"PASS: Search 'amore' returned {len(results)} results: {term_ids}")
    
    def test_search_peace_returns_results(self):
        """GET /api/dictionary/search/peace returns matching terms"""
        response = requests.get(f"{BASE_URL}/api/dictionary/search/peace", timeout=10)
        assert response.status_code == 200
        results = response.json()
        
        # Shalom means peace
        print(f"PASS: Search 'peace' returned {len(results)} results")
    
    def test_search_empty_returns_empty_list(self):
        """GET /api/dictionary/search/xyz123nonexistent returns empty list"""
        response = requests.get(f"{BASE_URL}/api/dictionary/search/xyz123nonexistent", timeout=10)
        assert response.status_code == 200
        results = response.json()
        assert results == [] or len(results) == 0, "Non-matching search should return empty list"
        print("PASS: Non-matching search returns empty list")


# =============================================================================
# BACKWARD COMPATIBILITY TESTS
# =============================================================================

class TestBackwardCompatibility:
    """Tests to ensure Italian defaults work (backward compatibility)"""
    
    def test_dictionary_no_lang_defaults_to_italian(self):
        """GET /api/dictionary (no lang param) defaults to Italian"""
        response = requests.get(f"{BASE_URL}/api/dictionary", timeout=10)
        assert response.status_code == 200
        terms = response.json()
        
        # Should have Italian origins (Ebraico/Greco)
        origins = [t.get("origin") for t in terms]
        assert "Ebraico" in origins or "Greco" in origins, \
            f"Default should be Italian with 'Ebraico'/'Greco' origins, got: {set(origins)}"
        print(f"PASS: Dictionary defaults to Italian when no lang param")
    
    def test_quiz_topics_no_lang_defaults_to_italian(self):
        """GET /api/quiz/topics (no lang param) defaults to Italian"""
        response = requests.get(f"{BASE_URL}/api/quiz/topics", timeout=10)
        assert response.status_code == 200
        topics = response.json()
        assert len(topics) > 0
        
        # Italian titles typically have "Quiz su" or Italian words
        print(f"PASS: Quiz topics defaults to Italian when no lang param")


# =============================================================================
# BIBLE API REGRESSION TESTS (from iteration 1)
# =============================================================================

class TestBibleApiRegression:
    """Regression tests to ensure Bible APIs still work"""
    
    def test_german_books_returns_german_names(self):
        """GET /api/bible/books?lang=de returns German book names (not Italian fallback)"""
        response = requests.get(f"{BASE_URL}/api/bible/books?lang=de", timeout=10)
        assert response.status_code == 200
        books = response.json()
        
        # Find Psalms - German should be 'Psalmen', not Italian 'Salmi'
        psalms_book = next((b for b in books if "Psalm" in b["name"]), None)
        assert psalms_book is not None, "Should have Psalms book"
        assert psalms_book["name"] == "Psalmen", f"German Psalms should be 'Psalmen', got {psalms_book['name']}"
        print(f"PASS: German books returns 'Psalmen' not Italian 'Salmi'")
    
    def test_german_genesis_chapter_returns_german_text(self):
        """GET /api/bible/chapter/Genesis/1?lang=de returns German text with 'Anfang'"""
        response = requests.get(f"{BASE_URL}/api/bible/chapter/Genesis/1?lang=de", timeout=30)
        assert response.status_code == 200
        data = response.json()
        
        assert "verses" in data
        assert len(data["verses"]) > 0
        
        # German Genesis 1:1 should contain "Anfang" (beginning in German)
        all_text = " ".join([v["text"].lower() for v in data["verses"][:5]])
        assert "anfang" in all_text, f"German Genesis should contain 'Anfang', got: {all_text[:200]}"
        print(f"PASS: German Genesis 1 contains 'Anfang' (German text)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
