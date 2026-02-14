"""
Test Online Users & Community Features for Iteration 14

Tests:
- /api/user/heartbeat - Send heartbeat to track online status
- /api/community/online-users - Get list of online users
- /api/community/messages - Community messaging
- Authentication flows for these endpoints
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://amen-community-hub.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "testbible@cibospirituale.it"
TEST_PASSWORD = "Test123!"


class TestOnlineUsersFeature:
    """Tests for online users tracking feature"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        return data.get("session_token")
    
    def test_heartbeat_requires_auth(self):
        """Heartbeat endpoint should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/user/heartbeat",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 401, f"Expected 401 unauthorized, got {response.status_code}"
        print("✓ Heartbeat requires authentication")
    
    def test_heartbeat_with_valid_auth(self, auth_token):
        """Heartbeat should work with valid authentication"""
        response = requests.post(
            f"{BASE_URL}/api/user/heartbeat",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {auth_token}"
            }
        )
        assert response.status_code == 200, f"Heartbeat failed: {response.text}"
        data = response.json()
        assert data.get("status") == "ok", f"Expected status 'ok', got {data}"
        print("✓ Heartbeat works with valid auth")
    
    def test_online_users_list_no_auth_required(self):
        """Online users list should be accessible without authentication"""
        response = requests.get(f"{BASE_URL}/api/community/online-users")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "online_count" in data, "Response should have online_count"
        assert "users" in data, "Response should have users list"
        assert isinstance(data["users"], list), "Users should be a list"
        print(f"✓ Online users endpoint accessible - {data['online_count']} users online")
    
    def test_heartbeat_updates_presence(self, auth_token):
        """After heartbeat, user should appear in online users list"""
        # Send heartbeat first
        heartbeat_response = requests.post(
            f"{BASE_URL}/api/user/heartbeat",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {auth_token}"
            }
        )
        assert heartbeat_response.status_code == 200
        
        # Check online users
        online_response = requests.get(f"{BASE_URL}/api/community/online-users")
        assert online_response.status_code == 200
        
        data = online_response.json()
        assert data["online_count"] >= 1, "Should have at least 1 user online"
        
        # Check user structure
        if data["users"]:
            user = data["users"][0]
            assert "user_id" in user, "User should have user_id"
            assert "user_name" in user, "User should have user_name"
            assert "last_seen" in user, "User should have last_seen"
        
        print(f"✓ Heartbeat updates presence - {data['online_count']} user(s) online")


class TestCommunityMessages:
    """Tests for community messaging"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("session_token")
    
    def test_get_community_messages_requires_auth(self):
        """Get community messages should require authentication"""
        response = requests.get(
            f"{BASE_URL}/api/community/messages",
            params={"lang": "it"}
        )
        assert response.status_code == 401, f"Expected 401 unauthorized, got {response.status_code}"
        print("✓ Get community messages requires auth")
    
    def test_get_community_messages_with_auth(self, auth_token):
        """Get community messages should work with authentication"""
        response = requests.get(
            f"{BASE_URL}/api/community/messages",
            params={"lang": "it"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Messages should be a list"
        print(f"✓ Community messages retrieved - {len(data)} messages")
    
    def test_create_community_message_requires_auth(self):
        """Creating community message should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/community/messages",
            json={"content": "Test message", "language": "it", "message_type": "text"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Create community message requires auth")
    
    def test_create_community_message_with_auth(self, auth_token):
        """Creating community message with auth should work"""
        response = requests.post(
            f"{BASE_URL}/api/community/messages",
            json={
                "content": "TEST_Benedetto sia il Signore! 🙏",
                "language": "it",
                "message_type": "text"
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {auth_token}"
            }
        )
        assert response.status_code == 200, f"Create message failed: {response.text}"
        data = response.json()
        assert "message_id" in data, "Response should contain message_id"
        print(f"✓ Community message created with ID: {data['message_id']}")


class TestQuickActionRoutes:
    """Tests for quick action button routes that should exist"""
    
    def test_quiz_topics_endpoint(self):
        """Quiz topics endpoint should exist"""
        response = requests.get(f"{BASE_URL}/api/quiz/topics", params={"lang": "it"})
        assert response.status_code == 200, f"Quiz topics endpoint failed: {response.status_code}"
        print("✓ Quiz topics endpoint works")
    
    def test_dictionary_endpoint(self):
        """Dictionary endpoint should exist"""
        response = requests.get(f"{BASE_URL}/api/dictionary", params={"lang": "it"})
        assert response.status_code == 200, f"Dictionary endpoint failed: {response.status_code}"
        print("✓ Dictionary endpoint works")
    
    def test_groups_endpoint_requires_auth(self):
        """Groups endpoint for creating group requires auth"""
        response = requests.post(
            f"{BASE_URL}/api/groups",
            json={"name": "Test", "description": "Test", "topic": "prayer"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Groups create requires auth")
    
    def test_journal_requires_auth(self):
        """Journal endpoint requires auth"""
        response = requests.get(f"{BASE_URL}/api/journal")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Journal requires auth")


class TestNotificationServiceBackend:
    """Tests for notification-related backend functionality"""
    
    def test_daily_verse_endpoint(self):
        """Daily verse endpoint should work (used by notification service)"""
        response = requests.get(
            f"{BASE_URL}/api/bible/daily-verse",
            params={"lang": "it"}
        )
        assert response.status_code == 200, f"Daily verse failed: {response.status_code}"
        data = response.json()
        assert "text" in data or "verses" in data, "Daily verse should have text content"
        print(f"✓ Daily verse endpoint works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
