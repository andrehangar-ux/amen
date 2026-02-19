"""
Backend tests for Community & Private Chat features:
- GET /api/community/users - returns all users with is_online status
- POST /api/users/heartbeat - marks user as online
- GET /api/users/online - returns online users
- POST /api/private-messages - sends a private message
- GET /api/private-messages/conversations - lists conversations
- GET /api/private-messages/{other_user_id} - gets messages in conversation
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://spirit-study-update.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "testbible@cibospirituale.it"
TEST_PASSWORD = "Test123!"

# Target user for private message testing
TARGET_USER_ID = "user_3acb0d89385a"  # Desire


class TestCommunityAndChatAPIs:
    """Test suite for community and private chat features"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "session_token" in data, "No session_token in login response"
        return data["session_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Auth headers for requests"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    # ==================== HEARTBEAT TESTS ====================
    
    def test_heartbeat_marks_user_online(self, auth_headers):
        """POST /api/users/heartbeat should mark user as online"""
        response = requests.post(f"{BASE_URL}/api/users/heartbeat", headers=auth_headers)
        assert response.status_code == 200, f"Heartbeat failed: {response.text}"
        data = response.json()
        assert data.get("status") == "ok", f"Expected status: ok, got: {data}"
        print(f"✅ Heartbeat successful: {data}")
    
    def test_heartbeat_requires_auth(self):
        """POST /api/users/heartbeat should require authentication"""
        response = requests.post(f"{BASE_URL}/api/users/heartbeat")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("✅ Heartbeat correctly requires auth")
    
    # ==================== ONLINE USERS TESTS ====================
    
    def test_get_online_users_returns_list(self, auth_headers):
        """GET /api/users/online should return online_count and users array"""
        # First send heartbeat to ensure at least one user is online
        requests.post(f"{BASE_URL}/api/users/heartbeat", headers=auth_headers)
        
        response = requests.get(f"{BASE_URL}/api/users/online", headers=auth_headers)
        assert response.status_code == 200, f"Get online users failed: {response.text}"
        data = response.json()
        
        assert "online_count" in data, "Missing online_count field"
        assert "users" in data, "Missing users field"
        assert isinstance(data["users"], list), "users should be a list"
        assert data["online_count"] >= 1, "Should have at least 1 user online (test user)"
        print(f"✅ Online users: count={data['online_count']}, users={len(data['users'])}")
    
    # ==================== COMMUNITY USERS TESTS ====================
    
    def test_community_users_returns_all_users(self, auth_headers):
        """GET /api/community/users should return all users (excluding current user) with is_online field"""
        response = requests.get(f"{BASE_URL}/api/community/users", headers=auth_headers)
        assert response.status_code == 200, f"Get community users failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Should return a list of users"
        assert len(data) > 0, "Should return at least one user"
        
        # Check structure of first user
        first_user = data[0]
        assert "user_id" in first_user, "User should have user_id"
        assert "name" in first_user, "User should have name"
        assert "is_online" in first_user, "User should have is_online field"
        assert isinstance(first_user["is_online"], bool), "is_online should be boolean"
        
        # Count online/offline users
        online_count = sum(1 for u in data if u["is_online"])
        offline_count = sum(1 for u in data if not u["is_online"])
        print(f"✅ Community users: total={len(data)}, online={online_count}, offline={offline_count}")
    
    def test_community_users_search(self, auth_headers):
        """GET /api/community/users?q=<name> should filter users by name"""
        response = requests.get(f"{BASE_URL}/api/community/users?q=Desire", headers=auth_headers)
        assert response.status_code == 200, f"Search failed: {response.text}"
        data = response.json()
        
        # Should find Desire if exists
        if len(data) > 0:
            assert any("desire" in u["name"].lower() for u in data), "Search should filter by name"
            print(f"✅ Community users search: found {len(data)} users matching 'Desire'")
        else:
            print("⚠️ No users found matching 'Desire' - may be expected if user doesn't exist")
    
    # ==================== PRIVATE MESSAGES TESTS ====================
    
    def test_send_private_message(self, auth_headers):
        """POST /api/private-messages should send a message"""
        test_message = f"Test message from pytest - {time.time()}"
        response = requests.post(
            f"{BASE_URL}/api/private-messages",
            headers=auth_headers,
            json={
                "receiver_id": TARGET_USER_ID,
                "content": test_message
            }
        )
        assert response.status_code == 200, f"Send PM failed: {response.text}"
        data = response.json()
        
        assert "message_id" in data, "Response should have message_id"
        assert data["content"] == test_message, "Message content should match"
        assert data["receiver_id"] == TARGET_USER_ID, "Receiver ID should match"
        print(f"✅ Private message sent: message_id={data['message_id']}")
    
    def test_send_message_to_nonexistent_user(self, auth_headers):
        """POST /api/private-messages to nonexistent user should return 404"""
        response = requests.post(
            f"{BASE_URL}/api/private-messages",
            headers=auth_headers,
            json={
                "receiver_id": "nonexistent_user_xyz",
                "content": "Test message"
            }
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✅ Send to nonexistent user correctly returns 404")
    
    def test_get_conversations(self, auth_headers):
        """GET /api/private-messages/conversations should list conversations"""
        response = requests.get(f"{BASE_URL}/api/private-messages/conversations", headers=auth_headers)
        assert response.status_code == 200, f"Get conversations failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Should return a list"
        
        if len(data) > 0:
            convo = data[0]
            assert "conversation_id" in convo, "Conversation should have conversation_id"
            assert "other_user_id" in convo, "Conversation should have other_user_id"
            assert "other_user_name" in convo, "Conversation should have other_user_name"
            assert "unread_count" in convo, "Conversation should have unread_count"
            print(f"✅ Conversations: {len(data)} found")
            for c in data[:3]:  # Show first 3
                print(f"   - {c['other_user_name']}: '{c.get('last_message', '')[:30]}...' (unread: {c['unread_count']})")
        else:
            print("⚠️ No conversations found")
    
    def test_get_private_messages_with_user(self, auth_headers):
        """GET /api/private-messages/{other_user_id} should return messages"""
        response = requests.get(f"{BASE_URL}/api/private-messages/{TARGET_USER_ID}", headers=auth_headers)
        assert response.status_code == 200, f"Get messages failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Should return a list of messages"
        
        if len(data) > 0:
            msg = data[0]
            assert "message_id" in msg, "Message should have message_id"
            assert "sender_id" in msg, "Message should have sender_id"
            assert "content" in msg, "Message should have content"
            assert "created_at" in msg, "Message should have created_at"
            print(f"✅ Messages with {TARGET_USER_ID}: {len(data)} messages found")
        else:
            print("⚠️ No messages found with target user")


class TestUserDataIntegrity:
    """Verify that the database has expected users"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Login and get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return {"Authorization": f"Bearer {response.json()['session_token']}"}
    
    def test_database_has_multiple_users(self, auth_headers):
        """Database should have multiple registered users (21 expected)"""
        response = requests.get(f"{BASE_URL}/api/community/users", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Should have users (excluding current user, so 20 expected if 21 total)
        assert len(data) >= 10, f"Expected at least 10 other users, got {len(data)}"
        print(f"✅ Database user count: {len(data)} users (excluding current user)")
        
        # Print some user names
        user_names = [u["name"] for u in data[:5]]
        print(f"   Sample users: {', '.join(user_names)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
