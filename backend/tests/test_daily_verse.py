"""
Test Daily Verse API - Iteration 37
Tests for the daily verse feature that changes every day of the year
and supports multiple languages (IT, ES, EN)
"""
import pytest
import requests
import os
from datetime import datetime, timezone

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://quiz-nav-build.preview.emergentagent.com')


class TestDailyVerseAPI:
    """Tests for /api/bible/daily-verse endpoint"""
    
    def test_daily_verse_italian(self):
        """Test daily verse returns correct structure in Italian"""
        response = requests.get(f"{BASE_URL}/api/bible/daily-verse?lang=it")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify response structure
        assert "reference" in data, "Response should contain 'reference'"
        assert "text" in data, "Response should contain 'text'"
        assert "language" in data, "Response should contain 'language'"
        assert "day_of_year" in data, "Response should contain 'day_of_year'"
        
        # Verify language is Italian
        assert data["language"] == "it", f"Expected language 'it', got {data['language']}"
        
        # Verify day_of_year is valid (1-365/366)
        assert 1 <= data["day_of_year"] <= 366, f"day_of_year should be 1-366, got {data['day_of_year']}"
        
        # Verify text is not empty
        assert len(data["text"]) > 0, "Verse text should not be empty"
        assert len(data["reference"]) > 0, "Verse reference should not be empty"
        
        print(f"SUCCESS: Italian verse - {data['reference']}: {data['text'][:50]}...")
    
    def test_daily_verse_spanish(self):
        """Test daily verse returns correct structure in Spanish"""
        response = requests.get(f"{BASE_URL}/api/bible/daily-verse?lang=es")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify response structure
        assert "reference" in data
        assert "text" in data
        assert "language" in data
        assert "day_of_year" in data
        
        # Verify language is Spanish
        assert data["language"] == "es", f"Expected language 'es', got {data['language']}"
        
        # Verify text is not empty
        assert len(data["text"]) > 0, "Verse text should not be empty"
        
        print(f"SUCCESS: Spanish verse - {data['reference']}: {data['text'][:50]}...")
    
    def test_daily_verse_english(self):
        """Test daily verse returns correct structure in English"""
        response = requests.get(f"{BASE_URL}/api/bible/daily-verse?lang=en")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify response structure
        assert "reference" in data
        assert "text" in data
        assert "language" in data
        assert "day_of_year" in data
        
        # Verify language is English
        assert data["language"] == "en", f"Expected language 'en', got {data['language']}"
        
        # Verify text is not empty
        assert len(data["text"]) > 0, "Verse text should not be empty"
        
        print(f"SUCCESS: English verse - {data['reference']}: {data['text'][:50]}...")
    
    def test_same_reference_all_languages(self):
        """Test that all languages return the same verse reference for the same day"""
        response_it = requests.get(f"{BASE_URL}/api/bible/daily-verse?lang=it")
        response_es = requests.get(f"{BASE_URL}/api/bible/daily-verse?lang=es")
        response_en = requests.get(f"{BASE_URL}/api/bible/daily-verse?lang=en")
        
        assert response_it.status_code == 200
        assert response_es.status_code == 200
        assert response_en.status_code == 200
        
        data_it = response_it.json()
        data_es = response_es.json()
        data_en = response_en.json()
        
        # All should have the same reference
        assert data_it["reference"] == data_es["reference"], \
            f"IT reference '{data_it['reference']}' != ES reference '{data_es['reference']}'"
        assert data_it["reference"] == data_en["reference"], \
            f"IT reference '{data_it['reference']}' != EN reference '{data_en['reference']}'"
        
        # All should have the same day_of_year
        assert data_it["day_of_year"] == data_es["day_of_year"] == data_en["day_of_year"], \
            "All languages should return the same day_of_year"
        
        # But texts should be different (different languages)
        # Note: Some short verses might be similar, so we just check they exist
        assert data_it["text"] != "" and data_es["text"] != "" and data_en["text"] != ""
        
        print(f"SUCCESS: All languages return same reference '{data_it['reference']}' for day {data_it['day_of_year']}")
    
    def test_day_of_year_matches_today(self):
        """Test that day_of_year matches the current day"""
        response = requests.get(f"{BASE_URL}/api/bible/daily-verse?lang=it")
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Get current day of year
        today = datetime.now(timezone.utc)
        expected_day = today.timetuple().tm_yday
        
        assert data["day_of_year"] == expected_day, \
            f"Expected day_of_year {expected_day}, got {data['day_of_year']}"
        
        print(f"SUCCESS: day_of_year {data['day_of_year']} matches today")
    
    def test_default_language_is_italian(self):
        """Test that default language (no param) returns Italian"""
        response = requests.get(f"{BASE_URL}/api/bible/daily-verse")
        
        assert response.status_code == 200
        
        data = response.json()
        
        assert data["language"] == "it", f"Default language should be 'it', got {data['language']}"
        
        print(f"SUCCESS: Default language is Italian")
    
    def test_unsupported_language_fallback(self):
        """Test that unsupported language falls back gracefully"""
        response = requests.get(f"{BASE_URL}/api/bible/daily-verse?lang=xyz")
        
        # Should still return 200 with fallback to Italian
        assert response.status_code == 200
        
        data = response.json()
        
        # Should have valid structure
        assert "reference" in data
        assert "text" in data
        assert "day_of_year" in data
        
        print(f"SUCCESS: Unsupported language handled gracefully")


class TestDailyVerseData:
    """Tests for daily verse data integrity"""
    
    def test_verse_text_not_empty(self):
        """Test that verse text is never empty"""
        for lang in ["it", "es", "en"]:
            response = requests.get(f"{BASE_URL}/api/bible/daily-verse?lang={lang}")
            assert response.status_code == 200
            
            data = response.json()
            assert len(data["text"].strip()) > 10, f"Verse text for {lang} should be substantial"
        
        print("SUCCESS: All verse texts are non-empty")
    
    def test_verse_reference_format(self):
        """Test that verse reference has valid format"""
        response = requests.get(f"{BASE_URL}/api/bible/daily-verse?lang=it")
        assert response.status_code == 200
        
        data = response.json()
        reference = data["reference"]
        
        # Reference should contain a colon (book chapter:verse format)
        # e.g., "Giovanni 6:35" or "Salmi 23:1"
        assert ":" in reference or "-" in reference, \
            f"Reference '{reference}' should contain ':' or '-' for verse notation"
        
        print(f"SUCCESS: Reference format is valid: {reference}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
