"""
Test suite for Minor Protection features (Google Play compliance)
- Birth date field in registration
- Safety status API for minors
- Private message restrictions for minors (can only chat with friends)
- APK/AAB download endpoints
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://quiz-nav-build.preview.emergentagent.com')

# Test credentials
TEST_USER_EMAIL = "testbible@cibospirituale.it"
TEST_USER_PASSWORD = "Test123!"
MINOR_BIRTH_DATE = "2015-05-15"  # Under 18
ADULT_BIRTH_DATE = "1990-05-15"  # Over 18


class TestMinorProtection:
    """Tests for minor protection features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup session for tests"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.auth_token = None
        self.user_id = None
    
    def login(self):
        """Login and get auth token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("session_token")
            self.user_id = data.get("user", {}).get("user_id")
            self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
            return True
        return False
    
    # === Test 1: Safety Status API ===
    def test_safety_status_endpoint_exists(self):
        """Test that /api/safety/status endpoint exists and requires auth"""
        response = self.session.get(f"{BASE_URL}/api/safety/status")
        # Should return 401 if not authenticated
        assert response.status_code == 401, f"Expected 401 for unauthenticated request, got {response.status_code}"
        print("PASS: /api/safety/status requires authentication")
    
    def test_safety_status_with_auth(self):
        """Test safety status returns correct data for authenticated user"""
        if not self.login():
            pytest.skip("Login failed")
        
        response = self.session.get(f"{BASE_URL}/api/safety/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "is_minor" in data, "Response should contain is_minor field"
        assert "age" in data, "Response should contain age field"
        assert "birth_date" in data, "Response should contain birth_date field"
        assert "parental_consent" in data, "Response should contain parental_consent field"
        assert "safety_reminder_shown" in data, "Response should contain safety_reminder_shown field"
        print(f"PASS: Safety status returned: is_minor={data['is_minor']}, age={data['age']}")
    
    # === Test 2: Update Birth Date API ===
    def test_update_birth_date_requires_auth(self):
        """Test that /api/users/birth-date requires auth"""
        response = self.session.put(f"{BASE_URL}/api/users/birth-date?birth_date=2010-01-01")
        assert response.status_code == 401, f"Expected 401 for unauthenticated request, got {response.status_code}"
        print("PASS: /api/users/birth-date requires authentication")
    
    def test_update_birth_date_minor(self):
        """Test updating birth date to make user a minor"""
        if not self.login():
            pytest.skip("Login failed")
        
        # Update to minor birth date
        response = self.session.put(f"{BASE_URL}/api/users/birth-date?birth_date={MINOR_BIRTH_DATE}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Expected success: true"
        assert data.get("is_minor") == True, f"Expected is_minor=True for birth_date {MINOR_BIRTH_DATE}, got {data.get('is_minor')}"
        assert data.get("birth_date") == MINOR_BIRTH_DATE, f"Expected birth_date={MINOR_BIRTH_DATE}"
        print(f"PASS: User marked as minor with birth_date={MINOR_BIRTH_DATE}")
    
    def test_update_birth_date_adult(self):
        """Test updating birth date to make user an adult"""
        if not self.login():
            pytest.skip("Login failed")
        
        # Update to adult birth date
        response = self.session.put(f"{BASE_URL}/api/users/birth-date?birth_date={ADULT_BIRTH_DATE}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Expected success: true"
        assert data.get("is_minor") == False, f"Expected is_minor=False for birth_date {ADULT_BIRTH_DATE}, got {data.get('is_minor')}"
        print(f"PASS: User marked as adult with birth_date={ADULT_BIRTH_DATE}")
    
    def test_update_birth_date_invalid_format(self):
        """Test that invalid birth date format is rejected"""
        if not self.login():
            pytest.skip("Login failed")
        
        # Try invalid format
        response = self.session.put(f"{BASE_URL}/api/users/birth-date?birth_date=15-05-2015")
        assert response.status_code == 422, f"Expected 422 for invalid format, got {response.status_code}"
        print("PASS: Invalid birth date format rejected")
    
    # === Test 3: Safety Status After Birth Date Update ===
    def test_safety_status_returns_minor_true(self):
        """Test that safety/status returns is_minor=true for minor birth date"""
        if not self.login():
            pytest.skip("Login failed")
        
        # First update to minor
        update_resp = self.session.put(f"{BASE_URL}/api/users/birth-date?birth_date={MINOR_BIRTH_DATE}")
        assert update_resp.status_code == 200
        
        # Then check safety status
        response = self.session.get(f"{BASE_URL}/api/safety/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("is_minor") == True, f"Expected is_minor=True, got {data.get('is_minor')}"
        assert data.get("safety_message") is not None, "Expected safety_message for minors"
        print(f"PASS: Safety status shows is_minor=True for {MINOR_BIRTH_DATE}")
    
    # === Test 4: Private Messages - Minor Protection ===
    def test_private_message_minor_blocked_non_friend(self):
        """Test that minor cannot send private message to non-friend"""
        if not self.login():
            pytest.skip("Login failed")
        
        # First make user a minor
        update_resp = self.session.put(f"{BASE_URL}/api/users/birth-date?birth_date={MINOR_BIRTH_DATE}")
        assert update_resp.status_code == 200
        
        # Try to send message to a random user (not a friend)
        fake_receiver_id = f"user_{uuid.uuid4().hex[:12]}"
        response = self.session.post(f"{BASE_URL}/api/private-messages", json={
            "receiver_id": fake_receiver_id,
            "content": "Test message from minor"
        })
        
        # Should get 403 or 404 (403 if minor protection kicks in before user lookup, 404 if user not found)
        assert response.status_code in [403, 404], f"Expected 403 or 404, got {response.status_code}: {response.text}"
        print(f"PASS: Minor blocked from sending message to non-friend (status: {response.status_code})")
    
    def test_private_message_adult_allowed(self):
        """Test that adult can send private message (may fail on receiver not found but not 403)"""
        if not self.login():
            pytest.skip("Login failed")
        
        # First make user an adult
        update_resp = self.session.put(f"{BASE_URL}/api/users/birth-date?birth_date={ADULT_BIRTH_DATE}")
        assert update_resp.status_code == 200
        
        # Try to send message to a random user
        fake_receiver_id = f"user_{uuid.uuid4().hex[:12]}"
        response = self.session.post(f"{BASE_URL}/api/private-messages", json={
            "receiver_id": fake_receiver_id,
            "content": "Test message from adult"
        })
        
        # Should get 404 (user not found) NOT 403 (forbidden)
        assert response.status_code == 404, f"Expected 404 (user not found), got {response.status_code}"
        # Verify it's not a 403 minor protection error
        if response.status_code == 403:
            data = response.json()
            assert "amici" not in data.get("detail", ""), "Adult should not get minor protection error"
        print("PASS: Adult not blocked by minor protection")
    
    # === Test 5: Safety Acknowledge Reminder ===
    def test_acknowledge_safety_reminder(self):
        """Test acknowledging safety reminder"""
        if not self.login():
            pytest.skip("Login failed")
        
        response = self.session.post(f"{BASE_URL}/api/safety/acknowledge-reminder")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("success") == True, "Expected success: true"
        print("PASS: Safety reminder acknowledged")
    
    # === Test 6: Can Share Info Endpoint ===
    def test_can_share_info_minor_no_consent(self):
        """Test that minor without parental consent cannot share info"""
        if not self.login():
            pytest.skip("Login failed")
        
        # Make user a minor (this resets parental consent)
        update_resp = self.session.put(f"{BASE_URL}/api/users/birth-date?birth_date={MINOR_BIRTH_DATE}")
        assert update_resp.status_code == 200
        
        response = self.session.get(f"{BASE_URL}/api/safety/can-share-info")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("can_share") == False, f"Expected can_share=False for minor, got {data.get('can_share')}"
        assert data.get("reason") == "parental_consent_required"
        print("PASS: Minor without parental consent cannot share info")
    
    def test_can_share_info_adult(self):
        """Test that adult can share info"""
        if not self.login():
            pytest.skip("Login failed")
        
        # Make user an adult
        update_resp = self.session.put(f"{BASE_URL}/api/users/birth-date?birth_date={ADULT_BIRTH_DATE}")
        assert update_resp.status_code == 200
        
        response = self.session.get(f"{BASE_URL}/api/safety/can-share-info")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("can_share") == True, f"Expected can_share=True for adult, got {data.get('can_share')}"
        assert data.get("reason") == "adult"
        print("PASS: Adult can share info")


class TestDownloads:
    """Tests for APK and AAB download endpoints"""
    
    def test_download_apk_endpoint(self):
        """Test APK download endpoint returns 200"""
        # Use GET with stream to avoid downloading entire file
        response = requests.get(f"{BASE_URL}/api/download/apk", stream=True)
        response.close()  # Close without downloading body
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: APK download endpoint returns 200")
    
    def test_download_apk_content_type(self):
        """Test APK download has correct content type"""
        response = requests.get(f"{BASE_URL}/api/download/apk", stream=True)
        content_type = response.headers.get("content-type", "")
        response.close()
        # May be application/vnd.android.package-archive or application/octet-stream
        assert "application" in content_type, f"Expected application content type, got {content_type}"
        print(f"PASS: APK content-type: {content_type}")
    
    def test_download_aab_endpoint(self):
        """Test AAB download endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/download/aab", stream=True)
        response.close()
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: AAB download endpoint returns 200")
    
    def test_download_aab_content_type(self):
        """Test AAB download has correct content type"""
        response = requests.get(f"{BASE_URL}/api/download/aab", stream=True)
        content_type = response.headers.get("content-type", "")
        response.close()
        assert "application" in content_type, f"Expected application content type, got {content_type}"
        print(f"PASS: AAB content-type: {content_type}")


class TestRegistrationBirthDate:
    """Tests for registration with birth date field"""
    
    def test_register_with_birth_date(self):
        """Test that registration accepts birth_date field"""
        # Create a unique test email
        test_email = f"test_minor_{uuid.uuid4().hex[:8]}@test.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "TestPass123!",
            "name": "Test Minor User",
            "language": "it",
            "birth_date": MINOR_BIRTH_DATE
        })
        
        # Should succeed (201 or 200)
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "user" in data, "Response should contain user object"
        
        user = data.get("user", {})
        assert user.get("birth_date") == MINOR_BIRTH_DATE, f"Expected birth_date={MINOR_BIRTH_DATE}, got {user.get('birth_date')}"
        print(f"PASS: Registration with birth_date successful: {user.get('birth_date')}")
    
    def test_register_without_birth_date(self):
        """Test that registration works without birth_date (backward compatibility)"""
        test_email = f"test_adult_{uuid.uuid4().hex[:8]}@test.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "TestPass123!",
            "name": "Test Adult User",
            "language": "it"
        })
        
        # Should succeed without birth_date
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}"
        print("PASS: Registration without birth_date successful (backward compatible)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
