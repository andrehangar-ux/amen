"""
Iteration 21 - Test new features:
1. Online users (heartbeat + online list)
2. Private messages (send, conversations, messages)
3. AI Dictionary Search
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', os.environ.get('EXPO_PUBLIC_BACKEND_URL', '')).rstrip('/')

# Test credentials
TEST_USER_EMAIL = "testbible@cibospirituale.it"
TEST_USER_PASSWORD = "Test123!"

# Second test user for private messaging tests
SECOND_USER_EMAIL = f"test_pm_{uuid.uuid4().hex[:8]}@test.com"
SECOND_USER_PASSWORD = "Test123!"
SECOND_USER_NAME = "PM Test User"


class TestAuthSetup:
    """Authentication setup tests"""
    
    @pytest.fixture(scope="class")
    def session(self):
        """Create requests session"""
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        return s
    
    def test_login_main_user(self, session):
        """Login with main test user"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "session_token" in data
        # Store token for class
        session.headers.update({"Authorization": f"Bearer {data['session_token']}"})
        TestAuthSetup.main_user_token = data['session_token']
        TestAuthSetup.main_user_id = data['user']['user_id']
        print(f"✓ Main user logged in: {TEST_USER_EMAIL}")


class TestHeartbeatAndOnlineUsers:
    """Test /api/users/heartbeat and /api/users/online endpoints"""
    
    @pytest.fixture
    def auth_session(self):
        """Session with auth token"""
        s = requests.Session()
        s.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TestAuthSetup.main_user_token}"
        })
        return s
    
    def test_heartbeat_returns_ok(self, auth_session):
        """POST /api/users/heartbeat should return {status: ok}"""
        response = auth_session.post(f"{BASE_URL}/api/users/heartbeat")
        assert response.status_code == 200, f"Heartbeat failed: {response.text}"
        data = response.json()
        assert data.get("status") == "ok", f"Expected status: ok, got: {data}"
        print("✓ Heartbeat returned status: ok")
    
    def test_get_online_users(self, auth_session):
        """GET /api/users/online should return list of online users"""
        response = auth_session.get(f"{BASE_URL}/api/users/online")
        assert response.status_code == 200, f"Get online users failed: {response.text}"
        data = response.json()
        assert "online_count" in data, "Missing online_count in response"
        assert "users" in data, "Missing users in response"
        assert isinstance(data["users"], list), "users should be a list"
        print(f"✓ Online users: {data['online_count']} users online")
        # After heartbeat, current user should be online
        user_ids = [u["user_id"] for u in data["users"]]
        assert TestAuthSetup.main_user_id in user_ids, "Current user should be online after heartbeat"
        print("✓ Current user appears in online users list")


class TestPrivateMessages:
    """Test private messaging endpoints"""
    
    @pytest.fixture(scope="class")
    def second_user_session(self):
        """Create and login second test user"""
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        
        # Register second user
        register_resp = s.post(f"{BASE_URL}/api/auth/register", json={
            "email": SECOND_USER_EMAIL,
            "password": SECOND_USER_PASSWORD,
            "name": SECOND_USER_NAME,
            "language": "it"
        })
        
        if register_resp.status_code == 200:
            data = register_resp.json()
            s.headers.update({"Authorization": f"Bearer {data['session_token']}"})
            TestPrivateMessages.second_user_id = data['user']['user_id']
            TestPrivateMessages.second_user_token = data['session_token']
            print(f"✓ Second user registered: {SECOND_USER_EMAIL}")
        elif register_resp.status_code == 400 and "già registrata" in register_resp.text:
            # User exists, try login
            login_resp = s.post(f"{BASE_URL}/api/auth/login", json={
                "email": SECOND_USER_EMAIL,
                "password": SECOND_USER_PASSWORD
            })
            if login_resp.status_code == 200:
                data = login_resp.json()
                s.headers.update({"Authorization": f"Bearer {data['session_token']}"})
                TestPrivateMessages.second_user_id = data['user']['user_id']
                TestPrivateMessages.second_user_token = data['session_token']
                print(f"✓ Second user logged in: {SECOND_USER_EMAIL}")
            else:
                pytest.skip(f"Could not login second user: {login_resp.text}")
        else:
            pytest.skip(f"Could not register second user: {register_resp.text}")
        
        return s
    
    @pytest.fixture
    def main_user_session(self):
        """Session for main user"""
        s = requests.Session()
        s.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TestAuthSetup.main_user_token}"
        })
        return s
    
    def test_send_private_message(self, main_user_session, second_user_session):
        """POST /api/private-messages - send message to second user"""
        second_id = TestPrivateMessages.second_user_id
        message_content = f"Test message from iteration 21 - {uuid.uuid4().hex[:8]}"
        
        response = main_user_session.post(f"{BASE_URL}/api/private-messages", json={
            "receiver_id": second_id,
            "content": message_content
        })
        assert response.status_code == 200, f"Send message failed: {response.text}"
        data = response.json()
        assert data.get("content") == message_content, "Message content mismatch"
        assert data.get("receiver_id") == second_id, "Receiver ID mismatch"
        assert "message_id" in data, "Missing message_id"
        print(f"✓ Private message sent successfully: {data['message_id']}")
        TestPrivateMessages.test_message_id = data['message_id']
        TestPrivateMessages.test_message_content = message_content
    
    def test_get_conversations_sender(self, main_user_session, second_user_session):
        """GET /api/private-messages/conversations - check sender has conversation"""
        # First ensure a message is sent
        if not hasattr(TestPrivateMessages, 'test_message_id'):
            self.test_send_private_message(main_user_session, second_user_session)
        
        response = main_user_session.get(f"{BASE_URL}/api/private-messages/conversations")
        assert response.status_code == 200, f"Get conversations failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Conversations should be a list"
        
        # Find conversation with second user
        conv = next((c for c in data if c.get("other_user_id") == TestPrivateMessages.second_user_id), None)
        assert conv is not None, "Conversation with second user not found"
        assert "last_message" in conv, "Missing last_message"
        assert "other_user_name" in conv, "Missing other_user_name"
        print(f"✓ Sender sees conversation with: {conv['other_user_name']}")
    
    def test_get_conversations_receiver(self, second_user_session):
        """GET /api/private-messages/conversations - check receiver has conversation"""
        s = requests.Session()
        s.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TestPrivateMessages.second_user_token}"
        })
        
        response = s.get(f"{BASE_URL}/api/private-messages/conversations")
        assert response.status_code == 200, f"Get conversations failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Conversations should be a list"
        
        # Find conversation with main user
        conv = next((c for c in data if c.get("other_user_id") == TestAuthSetup.main_user_id), None)
        assert conv is not None, "Conversation with main user not found in receiver's list"
        print(f"✓ Receiver sees conversation with main user")
    
    def test_get_private_messages_in_conversation(self, main_user_session, second_user_session):
        """GET /api/private-messages/{other_user_id} - get messages in conversation"""
        second_id = TestPrivateMessages.second_user_id
        
        response = main_user_session.get(f"{BASE_URL}/api/private-messages/{second_id}")
        assert response.status_code == 200, f"Get messages failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Messages should be a list"
        assert len(data) > 0, "Should have at least one message"
        
        # Check message structure
        msg = data[0]
        assert "message_id" in msg, "Missing message_id"
        assert "content" in msg, "Missing content"
        assert "sender_id" in msg, "Missing sender_id"
        assert "receiver_id" in msg, "Missing receiver_id"
        assert "created_at" in msg, "Missing created_at"
        print(f"✓ Retrieved {len(data)} messages in conversation")
    
    def test_send_message_to_nonexistent_user(self, main_user_session):
        """POST /api/private-messages - should fail for nonexistent user"""
        response = main_user_session.post(f"{BASE_URL}/api/private-messages", json={
            "receiver_id": "nonexistent_user_12345",
            "content": "This should fail"
        })
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print("✓ Correctly rejected message to nonexistent user")


class TestAIDictionarySearch:
    """Test AI-powered dictionary search endpoint"""
    
    @pytest.fixture
    def session(self):
        """Unauthenticated session for dictionary search"""
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        return s
    
    def test_ai_search_italian_term(self, session):
        """GET /api/dictionary/ai-search/salvezza?lang=it - AI search in Italian"""
        response = session.get(f"{BASE_URL}/api/dictionary/ai-search/salvezza?lang=it", timeout=30)
        assert response.status_code == 200, f"AI search failed: {response.text}"
        data = response.json()
        
        assert "source" in data, "Missing source field"
        assert "term" in data, "Missing term field"
        
        term = data["term"]
        # AI should return term info
        assert "term" in term or "found" in term, "Term should have 'term' or 'found' field"
        if term.get("found", True):  # Default to True if not present
            assert "meaning" in term or "description" in term, "Term should have meaning or description"
            print(f"✓ AI search for 'salvezza' (Italian): {term.get('meaning', term.get('description', 'N/A'))[:100]}...")
        else:
            print(f"✓ AI search returned not found: {term}")
    
    def test_ai_search_english_term(self, session):
        """GET /api/dictionary/ai-search/agape?lang=en - AI search in English"""
        response = session.get(f"{BASE_URL}/api/dictionary/ai-search/agape?lang=en", timeout=30)
        assert response.status_code == 200, f"AI search failed: {response.text}"
        data = response.json()
        
        assert "source" in data, "Missing source field"
        assert "term" in data, "Missing term field"
        
        term = data["term"]
        print(f"✓ AI search for 'agape' (English) - source: {data['source']}")
        if term.get("found", True):
            if "meaning" in term:
                print(f"  Meaning: {term['meaning'][:100]}...")
            if "description" in term:
                print(f"  Description: {term['description'][:100]}...")
    
    def test_ai_search_unknown_term(self, session):
        """GET /api/dictionary/ai-search/{random} - should handle unknown terms"""
        random_term = f"xyzabc{uuid.uuid4().hex[:4]}"
        response = session.get(f"{BASE_URL}/api/dictionary/ai-search/{random_term}?lang=it", timeout=30)
        assert response.status_code == 200, f"AI search should not fail for unknown terms: {response.text}"
        data = response.json()
        assert "term" in data, "Should return term info"
        term = data["term"]
        # Unknown term should return found=false or a suggestion
        if "found" in term:
            print(f"✓ Unknown term handled: found={term['found']}")
        else:
            print(f"✓ Unknown term returned some result")


class TestRegressions:
    """Regression tests for existing functionality"""
    
    @pytest.fixture
    def session(self):
        """Session without auth"""
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        return s
    
    def test_login_with_credentials(self, session):
        """POST /api/auth/login - should still work"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200, f"Login regression failed: {response.text}"
        data = response.json()
        assert "session_token" in data
        assert "user" in data
        print("✓ Login with credentials still working")


# Run order: setup first, then features, then regressions
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
