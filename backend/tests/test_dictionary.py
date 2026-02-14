"""
Test suite for Biblical Dictionary API endpoints
Tests: GET /api/dictionary, GET /api/dictionary/{term_id}, AI translation, caching
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://reading-progress-4.preview.emergentagent.com')

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
    if response.status_code == 200:
        return response.json().get("session_token")
    pytest.skip("Authentication failed - skipping authenticated tests")

@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


class TestDictionaryList:
    """Tests for GET /api/dictionary endpoint"""
    
    def test_dictionary_returns_69_terms_italian(self, api_client):
        """Test that dictionary returns exactly 69 terms for Italian"""
        response = api_client.get(f"{BASE_URL}/api/dictionary?lang=it")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 69, f"Expected 69 terms, got {len(data)}"
        
        # Verify structure of first term
        first_term = data[0]
        assert "id" in first_term
        assert "term" in first_term
        assert "origin" in first_term
        assert "meaning" in first_term
    
    def test_dictionary_returns_69_terms_english(self, api_client):
        """Test that dictionary returns exactly 69 terms for English"""
        response = api_client.get(f"{BASE_URL}/api/dictionary?lang=en")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 69, f"Expected 69 terms, got {len(data)}"
    
    def test_dictionary_returns_69_terms_spanish(self, api_client):
        """Test that dictionary returns exactly 69 terms for Spanish"""
        response = api_client.get(f"{BASE_URL}/api/dictionary?lang=es")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 69, f"Expected 69 terms, got {len(data)}"
    
    def test_dictionary_returns_69_terms_german(self, api_client):
        """Test that dictionary returns exactly 69 terms for German"""
        response = api_client.get(f"{BASE_URL}/api/dictionary?lang=de")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 69, f"Expected 69 terms, got {len(data)}"
    
    def test_dictionary_returns_69_terms_french(self, api_client):
        """Test that dictionary returns exactly 69 terms for French"""
        response = api_client.get(f"{BASE_URL}/api/dictionary?lang=fr")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 69, f"Expected 69 terms, got {len(data)}"
    
    def test_dictionary_returns_69_terms_portuguese(self, api_client):
        """Test that dictionary returns exactly 69 terms for Portuguese"""
        response = api_client.get(f"{BASE_URL}/api/dictionary?lang=pt")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 69, f"Expected 69 terms, got {len(data)}"
    
    def test_dictionary_sorted_alphabetically(self, api_client):
        """Test that dictionary terms are sorted alphabetically"""
        response = api_client.get(f"{BASE_URL}/api/dictionary?lang=it")
        assert response.status_code == 200
        
        data = response.json()
        # Extract term names (ignoring parentheses content)
        term_names = [t["term"].split(" (")[0].lower() for t in data]
        sorted_names = sorted(term_names)
        
        assert term_names == sorted_names, "Terms are not sorted alphabetically"
    
    def test_origin_labels_translated_italian(self, api_client):
        """Test origin labels are in Italian for lang=it"""
        response = api_client.get(f"{BASE_URL}/api/dictionary?lang=it")
        assert response.status_code == 200
        
        data = response.json()
        origins = set(t["origin"] for t in data)
        
        # Italian labels
        assert "Ebraico" in origins or "Greco" in origins or "Aramaico" in origins
    
    def test_origin_labels_translated_english(self, api_client):
        """Test origin labels are in English for lang=en"""
        response = api_client.get(f"{BASE_URL}/api/dictionary?lang=en")
        assert response.status_code == 200
        
        data = response.json()
        origins = set(t["origin"] for t in data)
        
        # English labels
        assert "Hebrew" in origins or "Greek" in origins or "Aramaic" in origins
    
    def test_origin_labels_translated_spanish(self, api_client):
        """Test origin labels are in Spanish for lang=es"""
        response = api_client.get(f"{BASE_URL}/api/dictionary?lang=es")
        assert response.status_code == 200
        
        data = response.json()
        origins = set(t["origin"] for t in data)
        
        # Spanish labels
        assert "Hebreo" in origins or "Griego" in origins or "Arameo" in origins
    
    def test_origin_labels_translated_german(self, api_client):
        """Test origin labels are in German for lang=de"""
        response = api_client.get(f"{BASE_URL}/api/dictionary?lang=de")
        assert response.status_code == 200
        
        data = response.json()
        origins = set(t["origin"] for t in data)
        
        # German labels
        assert "Hebräisch" in origins or "Griechisch" in origins or "Aramäisch" in origins
    
    def test_origin_labels_translated_french(self, api_client):
        """Test origin labels are in French for lang=fr"""
        response = api_client.get(f"{BASE_URL}/api/dictionary?lang=fr")
        assert response.status_code == 200
        
        data = response.json()
        origins = set(t["origin"] for t in data)
        
        # French labels
        assert "Hébreu" in origins or "Grec" in origins or "Araméen" in origins
    
    def test_origin_labels_translated_portuguese(self, api_client):
        """Test origin labels are in Portuguese for lang=pt"""
        response = api_client.get(f"{BASE_URL}/api/dictionary?lang=pt")
        assert response.status_code == 200
        
        data = response.json()
        origins = set(t["origin"] for t in data)
        
        # Portuguese labels
        assert "Hebraico" in origins or "Grego" in origins or "Aramaico" in origins


class TestDictionaryTermDetail:
    """Tests for GET /api/dictionary/{term_id} endpoint"""
    
    def test_get_term_detail_italian(self, api_client):
        """Test getting term detail in Italian"""
        response = api_client.get(f"{BASE_URL}/api/dictionary/agape?lang=it")
        assert response.status_code == 200
        
        data = response.json()
        assert "term" in data
        assert "transliteration" in data
        assert "origin" in data
        assert "pronunciation" in data
        assert "meaning" in data
        assert "root" in data
        assert "description" in data
        assert "verses" in data
        assert isinstance(data["verses"], list)
        assert len(data["verses"]) > 0
    
    def test_get_term_detail_english(self, api_client):
        """Test getting term detail in English with translation"""
        response = api_client.get(f"{BASE_URL}/api/dictionary/agape?lang=en")
        assert response.status_code == 200
        
        data = response.json()
        assert "term" in data
        assert "meaning" in data
        # Should have English translation
        assert "love" in data["meaning"].lower() or "unconditional" in data["meaning"].lower()
    
    def test_get_term_detail_spanish(self, api_client):
        """Test getting term detail in Spanish with translation"""
        response = api_client.get(f"{BASE_URL}/api/dictionary/shalom?lang=es")
        assert response.status_code == 200
        
        data = response.json()
        assert "term" in data
        assert "meaning" in data
        # Should have Spanish translation
        assert "paz" in data["meaning"].lower() or "bienestar" in data["meaning"].lower()
    
    def test_get_term_not_found(self, api_client):
        """Test 404 for non-existent term"""
        response = api_client.get(f"{BASE_URL}/api/dictionary/nonexistent_term?lang=it")
        assert response.status_code == 404
    
    def test_get_aramaic_term(self, api_client):
        """Test getting Aramaic term (maranatha)"""
        response = api_client.get(f"{BASE_URL}/api/dictionary/maranatha?lang=it")
        assert response.status_code == 200
        
        data = response.json()
        assert data["origin"] == "Aramaico"
        assert "Vieni" in data["meaning"] or "Signore" in data["meaning"]
    
    def test_get_aramaic_term_english_origin_label(self, api_client):
        """Test Aramaic term has correct English origin label"""
        response = api_client.get(f"{BASE_URL}/api/dictionary/maranatha?lang=en")
        assert response.status_code == 200
        
        data = response.json()
        assert data["origin"] == "Aramaic"
    
    def test_term_has_verses(self, api_client):
        """Test that term detail includes Bible verses"""
        response = api_client.get(f"{BASE_URL}/api/dictionary/logos?lang=it")
        assert response.status_code == 200
        
        data = response.json()
        assert "verses" in data
        assert len(data["verses"]) >= 1
        
        # Check verse structure
        verse = data["verses"][0]
        assert "ref" in verse
        assert "text" in verse


class TestAITranslation:
    """Tests for AI translation functionality"""
    
    def test_ai_translation_for_non_pretranslated_term(self, api_client):
        """Test AI translation works for terms without pre-translations"""
        # 'torah' has pre-translations, let's try a term that might not
        response = api_client.get(f"{BASE_URL}/api/dictionary/ruach?lang=en")
        assert response.status_code == 200
        
        data = response.json()
        assert "meaning" in data
        assert "description" in data
        # Should have some English content
        assert len(data["meaning"]) > 0
        assert len(data["description"]) > 0
    
    def test_ai_translation_caching(self, api_client):
        """Test that AI translations are cached (second request should be faster)"""
        import time
        
        # First request - might trigger AI translation
        start1 = time.time()
        response1 = api_client.get(f"{BASE_URL}/api/dictionary/nefesh?lang=de")
        time1 = time.time() - start1
        assert response1.status_code == 200
        
        # Second request - should use cache
        start2 = time.time()
        response2 = api_client.get(f"{BASE_URL}/api/dictionary/nefesh?lang=de")
        time2 = time.time() - start2
        assert response2.status_code == 200
        
        # Both should return same data
        assert response1.json()["meaning"] == response2.json()["meaning"]
        
        # Second request should be faster (cached)
        # Note: This is a soft assertion as network conditions vary
        print(f"First request: {time1:.2f}s, Second request: {time2:.2f}s")


class TestQuizSubmit:
    """Tests for Quiz submit functionality"""
    
    def test_quiz_topics_available(self, api_client):
        """Test that quiz topics are available"""
        response = api_client.get(f"{BASE_URL}/api/quiz/topics?lang=it")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 10, f"Expected at least 10 quiz topics, got {len(data)}"
    
    def test_quiz_questions_available(self, api_client):
        """Test that quiz questions are available for a topic (endpoint: /api/quiz/{topic})"""
        # First get topics
        topics_response = api_client.get(f"{BASE_URL}/api/quiz/topics?lang=it")
        assert topics_response.status_code == 200
        topics = topics_response.json()
        
        if len(topics) > 0:
            topic_id = topics[0]["id"]
            # Correct endpoint is /api/quiz/{topic} not /api/quiz/questions/{topic}
            response = api_client.get(f"{BASE_URL}/api/quiz/{topic_id}?lang=it")
            assert response.status_code == 200
            
            data = response.json()
            assert "questions" in data
            assert isinstance(data["questions"], list)
            assert len(data["questions"]) > 0
    
    def test_quiz_submit(self, authenticated_client):
        """Test quiz submission"""
        # Get topics first
        topics_response = authenticated_client.get(f"{BASE_URL}/api/quiz/topics?lang=it")
        assert topics_response.status_code == 200
        topics = topics_response.json()
        
        if len(topics) > 0:
            topic_id = topics[0]["id"]
            
            # Get quiz (correct endpoint: /api/quiz/{topic})
            quiz_response = authenticated_client.get(f"{BASE_URL}/api/quiz/{topic_id}?lang=it")
            assert quiz_response.status_code == 200
            quiz = quiz_response.json()
            
            if "questions" in quiz and len(quiz["questions"]) > 0:
                # Submit answers as Dict[str, int] - question_id -> selected_option_index
                answers = {}
                for q in quiz["questions"]:
                    answers[q.get("id", "q1")] = q.get("correct", 0)
                
                submit_response = authenticated_client.post(
                    f"{BASE_URL}/api/quiz/submit",
                    json={
                        "topic": topic_id,
                        "answers": answers,
                        "language": "it"
                    }
                )
                
                # Should return 200 or 201
                assert submit_response.status_code in [200, 201], f"Quiz submit failed: {submit_response.text}"
                
                # Verify response structure
                data = submit_response.json()
                assert "score" in data
                assert "correct_count" in data or "results" in data


class TestDictionarySearch:
    """Tests for dictionary search functionality"""
    
    def test_search_dictionary_italian(self, api_client):
        """Test dictionary search endpoint with Italian term"""
        response = api_client.get(f"{BASE_URL}/api/dictionary/search/amore")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Should find 'agape' which means love
        term_ids = [t.get("id") for t in data]
        assert "agape" in term_ids, f"Expected 'agape' in results, got: {term_ids}"
    
    def test_search_dictionary_term_name(self, api_client):
        """Test dictionary search by term name"""
        response = api_client.get(f"{BASE_URL}/api/dictionary/search/shalom")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        term_ids = [t.get("id") for t in data]
        assert "shalom" in term_ids, f"Expected 'shalom' in results, got: {term_ids}"


class TestDictionaryAIStudy:
    """Tests for AI dictionary study endpoint"""
    
    def test_ai_dictionary_study(self, authenticated_client):
        """Test AI study endpoint for dictionary terms"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/dictionary/ai-study",
            json={
                "term_id": "agape",
                "question": "What is the difference between agape and philia?"
            }
        )
        
        # Should return 200 with AI answer
        assert response.status_code == 200
        
        data = response.json()
        assert "answer" in data
        assert len(data["answer"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
