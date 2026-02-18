"""
Test suite for Mood Check-in API - P0 Bug Fix Verification
Tests the exclude_ref functionality to ensure different verses are returned on consecutive calls

Test Coverage:
- POST /api/ai/mood-checkin with exclude_ref returns different verse
- Consecutive calls with same mood return different verses
- Backward compatibility (calls without exclude_ref)
- Different moods return appropriate verses
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "testbible@cibospirituale.it"
TEST_PASSWORD = "Test123!"


@pytest.fixture(scope="module")
def auth_token():
    """Login and get auth token for tests"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        headers={"Content-Type": "application/json"}
    )
    if response.status_code != 200:
        pytest.skip(f"Login failed with status {response.status_code}: {response.text}")
    
    data = response.json()
    return data.get("session_token")


@pytest.fixture
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }


class TestMoodCheckinExcludeRef:
    """P0 Bug Fix: Test that consecutive mood checkins return different verses"""
    
    def test_mood_checkin_returns_different_verses_with_exclude_ref(self, auth_headers):
        """5 consecutive calls with same mood + exclude_ref should return different verses"""
        mood = "felice"
        verse_refs = []
        last_ref = None
        
        for i in range(5):
            payload = {
                "mood": mood,
                "language": "it",
                "exclude_ref": last_ref  # Pass previous verse ref to exclude
            }
            
            response = requests.post(
                f"{BASE_URL}/api/ai/mood-checkin",
                json=payload,
                headers=auth_headers
            )
            
            assert response.status_code == 200, f"Call {i+1} failed: {response.text}"
            
            data = response.json()
            assert "verse" in data, f"Call {i+1}: No verse in response"
            assert "ref" in data["verse"], f"Call {i+1}: No ref in verse"
            assert "reflection" in data, f"Call {i+1}: No reflection in response"
            
            current_ref = data["verse"]["ref"]
            verse_refs.append(current_ref)
            
            # Verify exclude_ref worked - current ref should differ from last_ref
            if last_ref:
                assert current_ref != last_ref, f"Call {i+1}: Got same verse '{current_ref}' as previous call"
            
            last_ref = current_ref
            print(f"Call {i+1}: {current_ref}")
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        
        # Verify we got multiple different verses (at least 3 unique out of 5 calls)
        unique_refs = set(verse_refs)
        print(f"Verse refs received: {verse_refs}")
        print(f"Unique verses: {len(unique_refs)}")
        
        # Allow some duplication since there are limited verses per mood
        assert len(unique_refs) >= 3, f"Expected at least 3 unique verses, got {len(unique_refs)}: {verse_refs}"
    
    def test_mood_checkin_without_exclude_ref_backward_compatible(self, auth_headers):
        """Calls without exclude_ref should still work (backward compatibility)"""
        payload = {
            "mood": "triste",
            "language": "it"
            # No exclude_ref - testing backward compatibility
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai/mood-checkin",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Request failed: {response.text}"
        
        data = response.json()
        assert "verse" in data
        assert "ref" in data["verse"]
        assert "text" in data["verse"]
        assert "reflection" in data
        assert "mood" in data
        
        print(f"Backward compatible call returned: {data['verse']['ref']}")


class TestMoodCheckinDifferentMoods:
    """Test that different moods return appropriate verses"""
    
    @pytest.mark.parametrize("mood,expected_lang", [
        ("happy", "it"),  # English key maps to Italian mood
        ("sad", "it"),
        ("anxious", "it"),
        ("felice", "it"),  # Direct Italian key
        ("triste", "it"),
        ("ansioso", "it"),
    ])
    def test_different_moods_return_verses(self, auth_headers, mood, expected_lang):
        """Each mood type should return a relevant verse"""
        payload = {
            "mood": mood,
            "language": expected_lang
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai/mood-checkin",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Request for mood '{mood}' failed: {response.text}"
        
        data = response.json()
        assert "verse" in data
        assert "ref" in data["verse"]
        assert "text" in data["verse"]
        assert len(data["verse"]["text"]) > 10, "Verse text seems too short"
        
        print(f"Mood '{mood}' returned: {data['verse']['ref']}")


class TestMoodCheckinResponseStructure:
    """Test the response structure of mood-checkin API"""
    
    def test_response_contains_all_required_fields(self, auth_headers):
        """Verify response has all required fields"""
        payload = {
            "mood": "grato",
            "language": "it"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai/mood-checkin",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Check top-level fields
        assert "mood" in data, "Missing 'mood' field"
        assert "verse" in data, "Missing 'verse' field"
        assert "reflection" in data, "Missing 'reflection' field"
        
        # Check verse structure
        verse = data["verse"]
        assert "ref" in verse, "Missing 'ref' in verse"
        assert "text" in verse, "Missing 'text' in verse"
        
        # Verify data quality
        assert len(verse["ref"]) > 0, "Empty verse reference"
        assert len(verse["text"]) > 0, "Empty verse text"
        assert len(data["reflection"]) > 0, "Empty reflection"
        
        print(f"Response structure valid. Verse: {verse['ref']}, Reflection length: {len(data['reflection'])}")


class TestMoodCheckinAuth:
    """Test authentication requirements"""
    
    def test_mood_checkin_requires_auth(self):
        """Mood checkin should require authentication"""
        payload = {
            "mood": "felice",
            "language": "it"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai/mood-checkin",
            json=payload,
            headers={"Content-Type": "application/json"}
            # No Authorization header
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
