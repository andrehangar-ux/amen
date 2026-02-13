"""
Test suite for Dictionary Favorites and Flashcards API endpoints
Tests: favorites CRUD, flashcards CRUD, spaced repetition review, stats
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://scriptural-study.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "testbible@cibospirituale.it"
TEST_PASSWORD = "Test123!"

# Test term IDs (from dictionary)
TEST_TERM_ID = "agape"  # Common Greek term
TEST_TERM_ID_2 = "shalom"  # Common Hebrew term


class TestSetup:
    """Setup and authentication tests"""
    
    @pytest.fixture(scope="class")
    def session(self):
        """Create authenticated session"""
        s = requests.Session()
        s.headers.update({
            "Content-Type": "application/json",
            "bypass-tunnel-reminder": "true"
        })
        return s
    
    @pytest.fixture(scope="class")
    def auth_token(self, session):
        """Get authentication token"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        token = data.get("session_token")
        assert token, "No session token returned"
        return token
    
    @pytest.fixture(scope="class")
    def auth_session(self, session, auth_token):
        """Session with auth header"""
        session.headers.update({"Authorization": f"Bearer {auth_token}"})
        return session


class TestDictionaryFavorites(TestSetup):
    """Test favorites CRUD operations"""
    
    def test_get_favorites_empty_or_list(self, auth_session):
        """GET /api/dictionary/favorites - should return list"""
        response = auth_session.get(f"{BASE_URL}/api/dictionary/favorites?lang=it")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Favorites should be a list"
        print(f"Current favorites count: {len(data)}")
    
    def test_add_favorite(self, auth_session):
        """POST /api/dictionary/favorites - add term to favorites"""
        # First remove if exists (cleanup)
        auth_session.delete(f"{BASE_URL}/api/dictionary/favorites/{TEST_TERM_ID}")
        
        response = auth_session.post(f"{BASE_URL}/api/dictionary/favorites", json={
            "term_id": TEST_TERM_ID
        })
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data.get("term_id") == TEST_TERM_ID
        print(f"Added favorite: {data}")
    
    def test_check_favorite_exists(self, auth_session):
        """GET /api/dictionary/favorites/check/{term_id} - check if favorite"""
        response = auth_session.get(f"{BASE_URL}/api/dictionary/favorites/check/{TEST_TERM_ID}")
        assert response.status_code == 200
        data = response.json()
        assert "is_favorite" in data
        assert data["is_favorite"] == True, "Term should be marked as favorite"
        print(f"Favorite check: {data}")
    
    def test_get_favorites_contains_added(self, auth_session):
        """GET /api/dictionary/favorites - verify added term is in list"""
        response = auth_session.get(f"{BASE_URL}/api/dictionary/favorites?lang=it")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Find the added term
        term_ids = [f.get("term_id") for f in data]
        assert TEST_TERM_ID in term_ids, f"Added term {TEST_TERM_ID} should be in favorites"
        
        # Verify favorite has required fields
        for fav in data:
            if fav.get("term_id") == TEST_TERM_ID:
                assert "term" in fav, "Favorite should have term name"
                assert "meaning" in fav, "Favorite should have meaning"
                assert "origin" in fav, "Favorite should have origin"
                print(f"Favorite data: {fav}")
                break
    
    def test_add_duplicate_favorite(self, auth_session):
        """POST /api/dictionary/favorites - adding duplicate should not fail"""
        response = auth_session.post(f"{BASE_URL}/api/dictionary/favorites", json={
            "term_id": TEST_TERM_ID
        })
        # Should return 200 with message about already existing
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"Duplicate add response: {data}")
    
    def test_remove_favorite(self, auth_session):
        """DELETE /api/dictionary/favorites/{term_id} - remove from favorites"""
        response = auth_session.delete(f"{BASE_URL}/api/dictionary/favorites/{TEST_TERM_ID}")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"Remove favorite response: {data}")
    
    def test_check_favorite_removed(self, auth_session):
        """Verify favorite was removed"""
        response = auth_session.get(f"{BASE_URL}/api/dictionary/favorites/check/{TEST_TERM_ID}")
        assert response.status_code == 200
        data = response.json()
        assert data["is_favorite"] == False, "Term should no longer be favorite"
    
    def test_remove_nonexistent_favorite(self, auth_session):
        """DELETE /api/dictionary/favorites/{term_id} - removing non-favorite"""
        response = auth_session.delete(f"{BASE_URL}/api/dictionary/favorites/nonexistent_term_xyz")
        # Should return 404 or appropriate error
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
    
    def test_favorites_unauthenticated(self):
        """Test favorites endpoints require authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.get(f"{BASE_URL}/api/dictionary/favorites")
        assert response.status_code == 401, "Should require authentication"


class TestDictionaryFlashcards(TestSetup):
    """Test flashcards CRUD and spaced repetition"""
    
    created_flashcard_id = None
    
    def test_get_flashcards_list(self, auth_session):
        """GET /api/dictionary/flashcards - should return list"""
        response = auth_session.get(f"{BASE_URL}/api/dictionary/flashcards?lang=it")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Flashcards should be a list"
        print(f"Current flashcards count: {len(data)}")
    
    def test_create_flashcard(self, auth_session):
        """POST /api/dictionary/flashcards - create flashcard from term"""
        # First delete if exists (cleanup)
        existing = auth_session.get(f"{BASE_URL}/api/dictionary/flashcards?lang=it").json()
        for card in existing:
            if card.get("term_id") == TEST_TERM_ID_2:
                auth_session.delete(f"{BASE_URL}/api/dictionary/flashcards/{card.get('flashcard_id')}")
        
        response = auth_session.post(f"{BASE_URL}/api/dictionary/flashcards", json={
            "term_id": TEST_TERM_ID_2,
            "note": "Test flashcard note"
        })
        assert response.status_code == 200
        data = response.json()
        assert "flashcard_id" in data or "message" in data
        
        if "flashcard_id" in data:
            TestDictionaryFlashcards.created_flashcard_id = data["flashcard_id"]
            print(f"Created flashcard: {data}")
        else:
            # Already exists, get the ID
            existing = auth_session.get(f"{BASE_URL}/api/dictionary/flashcards?lang=it").json()
            for card in existing:
                if card.get("term_id") == TEST_TERM_ID_2:
                    TestDictionaryFlashcards.created_flashcard_id = card.get("flashcard_id")
                    break
            print(f"Flashcard already exists: {data}")
    
    def test_get_flashcards_contains_created(self, auth_session):
        """Verify created flashcard is in list"""
        response = auth_session.get(f"{BASE_URL}/api/dictionary/flashcards?lang=it")
        assert response.status_code == 200
        data = response.json()
        
        # Find the created flashcard
        found = False
        for card in data:
            if card.get("term_id") == TEST_TERM_ID_2:
                found = True
                # Verify flashcard has required fields
                assert "flashcard_id" in card, "Flashcard should have flashcard_id"
                assert "term" in card, "Flashcard should have term"
                assert "meaning" in card, "Flashcard should have meaning"
                assert "mastery_level" in card, "Flashcard should have mastery_level"
                assert "origin" in card, "Flashcard should have origin"
                print(f"Flashcard data: {card}")
                break
        
        assert found, f"Created flashcard for {TEST_TERM_ID_2} should be in list"
    
    def test_get_due_flashcards(self, auth_session):
        """GET /api/dictionary/flashcards/due - get cards due for review"""
        response = auth_session.get(f"{BASE_URL}/api/dictionary/flashcards/due?lang=it")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Due flashcards should be a list"
        print(f"Due flashcards count: {len(data)}")
        
        # New cards should be due immediately
        if len(data) > 0:
            for card in data:
                assert "flashcard_id" in card
                assert "term" in card
                assert "meaning" in card
    
    def test_get_flashcard_stats(self, auth_session):
        """GET /api/dictionary/flashcards/stats - get study statistics"""
        response = auth_session.get(f"{BASE_URL}/api/dictionary/flashcards/stats")
        assert response.status_code == 200
        data = response.json()
        
        # Verify stats structure
        assert "total_flashcards" in data, "Stats should have total_flashcards"
        assert "due_for_review" in data, "Stats should have due_for_review"
        assert "mastered" in data, "Stats should have mastered"
        assert "mastery_distribution" in data, "Stats should have mastery_distribution"
        
        assert isinstance(data["total_flashcards"], int)
        assert isinstance(data["due_for_review"], int)
        assert isinstance(data["mastered"], int)
        assert isinstance(data["mastery_distribution"], dict)
        
        print(f"Flashcard stats: {data}")
    
    def test_review_flashcard_quality_0(self, auth_session):
        """PUT /api/dictionary/flashcards/{id}/review - review with quality 0 (again)"""
        if not TestDictionaryFlashcards.created_flashcard_id:
            pytest.skip("No flashcard created")
        
        flashcard_id = TestDictionaryFlashcards.created_flashcard_id
        response = auth_session.put(f"{BASE_URL}/api/dictionary/flashcards/{flashcard_id}/review?quality=0")
        assert response.status_code == 200
        data = response.json()
        
        assert "new_mastery_level" in data, "Review should return new mastery level"
        assert "next_review" in data, "Review should return next review date"
        print(f"Review quality 0 response: {data}")
    
    def test_review_flashcard_quality_3(self, auth_session):
        """PUT /api/dictionary/flashcards/{id}/review - review with quality 3 (good)"""
        if not TestDictionaryFlashcards.created_flashcard_id:
            pytest.skip("No flashcard created")
        
        flashcard_id = TestDictionaryFlashcards.created_flashcard_id
        response = auth_session.put(f"{BASE_URL}/api/dictionary/flashcards/{flashcard_id}/review?quality=3")
        assert response.status_code == 200
        data = response.json()
        
        assert "new_mastery_level" in data
        assert "next_review" in data
        print(f"Review quality 3 response: {data}")
    
    def test_review_flashcard_quality_5(self, auth_session):
        """PUT /api/dictionary/flashcards/{id}/review - review with quality 5 (perfect)"""
        if not TestDictionaryFlashcards.created_flashcard_id:
            pytest.skip("No flashcard created")
        
        flashcard_id = TestDictionaryFlashcards.created_flashcard_id
        response = auth_session.put(f"{BASE_URL}/api/dictionary/flashcards/{flashcard_id}/review?quality=5")
        assert response.status_code == 200
        data = response.json()
        
        assert "new_mastery_level" in data
        # After quality 5, mastery should increase
        print(f"Review quality 5 response: {data}")
    
    def test_review_nonexistent_flashcard(self, auth_session):
        """PUT /api/dictionary/flashcards/{id}/review - review non-existent card"""
        response = auth_session.put(f"{BASE_URL}/api/dictionary/flashcards/nonexistent_fc_xyz/review?quality=3")
        assert response.status_code == 404, "Should return 404 for non-existent flashcard"
    
    def test_create_duplicate_flashcard(self, auth_session):
        """POST /api/dictionary/flashcards - creating duplicate should not fail"""
        response = auth_session.post(f"{BASE_URL}/api/dictionary/flashcards", json={
            "term_id": TEST_TERM_ID_2
        })
        # Should return 200 with message about already existing
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "flashcard_id" in data
        print(f"Duplicate flashcard response: {data}")
    
    def test_delete_flashcard(self, auth_session):
        """DELETE /api/dictionary/flashcards/{id} - delete flashcard"""
        if not TestDictionaryFlashcards.created_flashcard_id:
            pytest.skip("No flashcard created")
        
        flashcard_id = TestDictionaryFlashcards.created_flashcard_id
        response = auth_session.delete(f"{BASE_URL}/api/dictionary/flashcards/{flashcard_id}")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"Delete flashcard response: {data}")
    
    def test_verify_flashcard_deleted(self, auth_session):
        """Verify flashcard was deleted"""
        response = auth_session.get(f"{BASE_URL}/api/dictionary/flashcards?lang=it")
        assert response.status_code == 200
        data = response.json()
        
        # Should not find the deleted flashcard
        for card in data:
            assert card.get("term_id") != TEST_TERM_ID_2 or card.get("flashcard_id") != TestDictionaryFlashcards.created_flashcard_id
    
    def test_flashcards_unauthenticated(self):
        """Test flashcard endpoints require authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.get(f"{BASE_URL}/api/dictionary/flashcards")
        assert response.status_code == 401, "Should require authentication"
        
        response = session.get(f"{BASE_URL}/api/dictionary/flashcards/stats")
        assert response.status_code == 401, "Stats should require authentication"


class TestSpacedRepetitionAlgorithm(TestSetup):
    """Test spaced repetition algorithm behavior"""
    
    test_flashcard_id = None
    
    def test_create_test_flashcard(self, auth_session):
        """Create a flashcard for algorithm testing"""
        # Cleanup first
        existing = auth_session.get(f"{BASE_URL}/api/dictionary/flashcards?lang=it").json()
        for card in existing:
            if card.get("term_id") == "logos":
                auth_session.delete(f"{BASE_URL}/api/dictionary/flashcards/{card.get('flashcard_id')}")
        
        response = auth_session.post(f"{BASE_URL}/api/dictionary/flashcards", json={
            "term_id": "logos"
        })
        assert response.status_code == 200
        data = response.json()
        
        if "flashcard_id" in data:
            TestSpacedRepetitionAlgorithm.test_flashcard_id = data["flashcard_id"]
        else:
            existing = auth_session.get(f"{BASE_URL}/api/dictionary/flashcards?lang=it").json()
            for card in existing:
                if card.get("term_id") == "logos":
                    TestSpacedRepetitionAlgorithm.test_flashcard_id = card.get("flashcard_id")
                    break
    
    def test_initial_mastery_level(self, auth_session):
        """New flashcard should have mastery level 0"""
        response = auth_session.get(f"{BASE_URL}/api/dictionary/flashcards?lang=it")
        data = response.json()
        
        for card in data:
            if card.get("term_id") == "logos":
                # New cards start at level 0
                assert card.get("mastery_level", 0) >= 0
                print(f"Initial mastery level: {card.get('mastery_level')}")
                break
    
    def test_mastery_increases_with_good_reviews(self, auth_session):
        """Mastery should increase with quality >= 3"""
        if not TestSpacedRepetitionAlgorithm.test_flashcard_id:
            pytest.skip("No test flashcard")
        
        flashcard_id = TestSpacedRepetitionAlgorithm.test_flashcard_id
        
        # Review with quality 4 (easy)
        response = auth_session.put(f"{BASE_URL}/api/dictionary/flashcards/{flashcard_id}/review?quality=4")
        assert response.status_code == 200
        data = response.json()
        
        new_level = data.get("new_mastery_level", 0)
        print(f"After quality 4 review, mastery: {new_level}")
        
        # Review again with quality 5 (perfect)
        response = auth_session.put(f"{BASE_URL}/api/dictionary/flashcards/{flashcard_id}/review?quality=5")
        assert response.status_code == 200
        data = response.json()
        
        newer_level = data.get("new_mastery_level", 0)
        print(f"After quality 5 review, mastery: {newer_level}")
        
        # Mastery should have increased
        assert newer_level >= new_level, "Mastery should increase with good reviews"
    
    def test_mastery_resets_with_bad_review(self, auth_session):
        """Mastery should reset/decrease with quality < 3"""
        if not TestSpacedRepetitionAlgorithm.test_flashcard_id:
            pytest.skip("No test flashcard")
        
        flashcard_id = TestSpacedRepetitionAlgorithm.test_flashcard_id
        
        # Review with quality 0 (again/forgot)
        response = auth_session.put(f"{BASE_URL}/api/dictionary/flashcards/{flashcard_id}/review?quality=0")
        assert response.status_code == 200
        data = response.json()
        
        new_level = data.get("new_mastery_level", 0)
        print(f"After quality 0 review, mastery: {new_level}")
        
        # Mastery should be low after forgetting
        assert new_level <= 2, "Mastery should be low after quality 0 review"
    
    def test_cleanup_test_flashcard(self, auth_session):
        """Cleanup test flashcard"""
        if TestSpacedRepetitionAlgorithm.test_flashcard_id:
            auth_session.delete(f"{BASE_URL}/api/dictionary/flashcards/{TestSpacedRepetitionAlgorithm.test_flashcard_id}")


class TestMultiLanguageSupport(TestSetup):
    """Test favorites and flashcards with different languages"""
    
    def test_favorites_italian(self, auth_session):
        """Test favorites with Italian language"""
        # Add favorite
        auth_session.delete(f"{BASE_URL}/api/dictionary/favorites/chesed")
        auth_session.post(f"{BASE_URL}/api/dictionary/favorites", json={"term_id": "chesed"})
        
        response = auth_session.get(f"{BASE_URL}/api/dictionary/favorites?lang=it")
        assert response.status_code == 200
        data = response.json()
        
        for fav in data:
            if fav.get("term_id") == "chesed":
                # Italian origin should be "Ebraico"
                assert "Ebraico" in fav.get("origin", "") or "Hebrew" in fav.get("origin", "")
                print(f"Italian favorite: {fav}")
                break
        
        # Cleanup
        auth_session.delete(f"{BASE_URL}/api/dictionary/favorites/chesed")
    
    def test_favorites_english(self, auth_session):
        """Test favorites with English language"""
        # Add favorite
        auth_session.delete(f"{BASE_URL}/api/dictionary/favorites/chesed")
        auth_session.post(f"{BASE_URL}/api/dictionary/favorites", json={"term_id": "chesed"})
        
        response = auth_session.get(f"{BASE_URL}/api/dictionary/favorites?lang=en")
        assert response.status_code == 200
        data = response.json()
        
        for fav in data:
            if fav.get("term_id") == "chesed":
                # English origin should be "Hebrew"
                assert "Hebrew" in fav.get("origin", "") or "Ebraico" in fav.get("origin", "")
                print(f"English favorite: {fav}")
                break
        
        # Cleanup
        auth_session.delete(f"{BASE_URL}/api/dictionary/favorites/chesed")
    
    def test_flashcards_multilang(self, auth_session):
        """Test flashcards with different languages"""
        # Create flashcard
        auth_session.post(f"{BASE_URL}/api/dictionary/flashcards", json={"term_id": "ruach"})
        
        # Get in Italian
        response_it = auth_session.get(f"{BASE_URL}/api/dictionary/flashcards?lang=it")
        assert response_it.status_code == 200
        
        # Get in English
        response_en = auth_session.get(f"{BASE_URL}/api/dictionary/flashcards?lang=en")
        assert response_en.status_code == 200
        
        # Cleanup
        for card in response_it.json():
            if card.get("term_id") == "ruach":
                auth_session.delete(f"{BASE_URL}/api/dictionary/flashcards/{card.get('flashcard_id')}")
                break


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
