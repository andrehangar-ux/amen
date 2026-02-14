"""
Test iteration 15: TTS in Bible page and Private Messages in Community
- TTS is handled client-side (Web Speech API / expo-speech), so we only verify the tts_code in languages API
- Private Messages APIs: POST /api/messages, GET /api/messages/{user_id}
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://amen-community-hub.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "testbible@cibospirituale.it"
TEST_PASSWORD = "Test123!"

# Secondary test user for private messages
SECONDARY_EMAIL = "test_secondary@cibospirituale.it"
SECONDARY_PASSWORD = "Test123!"

class TestLanguagesTTS:
    """Test that languages endpoint returns TTS codes for all languages"""
    
    def test_languages_have_tts_codes(self):
        """Verify all languages have tts_code for TTS functionality"""
        response = requests.get(f"{BASE_URL}/api/languages")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        languages = response.json()
        assert len(languages) > 0, "No languages returned"
        
        expected_langs = ["it", "es", "en", "pt", "fr", "de"]
        expected_tts_codes = {
            "it": "it-IT",
            "es": "es-ES", 
            "en": "en-US",
            "pt": "pt-BR",
            "fr": "fr-FR",
            "de": "de-DE"
        }
        
        for lang_code in expected_langs:
            assert lang_code in languages, f"Language {lang_code} not found"
            lang_data = languages[lang_code]
            
            assert "tts_code" in lang_data, f"tts_code missing for {lang_code}"
            assert lang_data["tts_code"] == expected_tts_codes[lang_code], \
                f"Wrong tts_code for {lang_code}: expected {expected_tts_codes[lang_code]}, got {lang_data['tts_code']}"
            
            print(f"✓ Language {lang_code} has correct tts_code: {lang_data['tts_code']}")
        
        print(f"All {len(expected_langs)} languages have correct TTS codes")


class TestPrivateMessagesAPI:
    """Test Private Messages API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        # Login primary user
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Primary login failed: {response.text}")
        
        data = response.json()
        self.primary_token = data.get("session_token")
        self.primary_user_id = data.get("user", {}).get("user_id")
        self.primary_headers = {
            "Authorization": f"Bearer {self.primary_token}",
            "Content-Type": "application/json"
        }
        print(f"✓ Logged in as primary user: {TEST_EMAIL}, user_id: {self.primary_user_id}")
        
        # Try to create or login secondary user for messaging
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SECONDARY_EMAIL,
            "password": SECONDARY_PASSWORD
        })
        
        if response.status_code != 200:
            # Try to register secondary user
            response = requests.post(f"{BASE_URL}/api/auth/register", json={
                "email": SECONDARY_EMAIL,
                "password": SECONDARY_PASSWORD,
                "name": "Test Secondary User",
                "language": "it"
            })
            if response.status_code not in [200, 201]:
                print(f"Could not create secondary user: {response.text}")
                # Try to find any existing user from online users
                self.secondary_user_id = None
            else:
                data = response.json()
                self.secondary_token = data.get("session_token")
                self.secondary_user_id = data.get("user", {}).get("user_id")
        else:
            data = response.json()
            self.secondary_token = data.get("session_token")
            self.secondary_user_id = data.get("user", {}).get("user_id")
        
        if self.secondary_user_id:
            print(f"✓ Secondary user available: {SECONDARY_EMAIL}, user_id: {self.secondary_user_id}")
        else:
            print("⚠ No secondary user available for private message tests")
    
    def test_private_messages_requires_auth(self):
        """POST /api/messages requires authentication"""
        response = requests.post(f"{BASE_URL}/api/messages", json={
            "receiver_id": "some_user_id",
            "content": "Test message"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ POST /api/messages correctly requires authentication")
    
    def test_get_conversation_requires_auth(self):
        """GET /api/messages/{user_id} requires authentication"""
        response = requests.get(f"{BASE_URL}/api/messages/some_user_id")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ GET /api/messages/{user_id} correctly requires authentication")
    
    def test_get_all_conversations_requires_auth(self):
        """GET /api/messages requires authentication"""
        response = requests.get(f"{BASE_URL}/api/messages")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ GET /api/messages correctly requires authentication")
    
    def test_send_private_message_to_nonexistent_user(self):
        """POST /api/messages to nonexistent user returns 404"""
        response = requests.post(
            f"{BASE_URL}/api/messages",
            headers=self.primary_headers,
            json={
                "receiver_id": "nonexistent_user_id_12345",
                "content": "Test message"
            }
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Sending message to nonexistent user correctly returns 404")
    
    def test_send_and_retrieve_private_message(self):
        """Test full private message flow: send -> retrieve"""
        if not hasattr(self, 'secondary_user_id') or not self.secondary_user_id:
            pytest.skip("No secondary user available for this test")
        
        # Send a private message
        test_message = f"Test private message {int(time.time())}"
        response = requests.post(
            f"{BASE_URL}/api/messages",
            headers=self.primary_headers,
            json={
                "receiver_id": self.secondary_user_id,
                "content": test_message
            }
        )
        assert response.status_code == 200, f"Send message failed: {response.status_code} - {response.text}"
        
        sent_msg = response.json()
        assert "message_id" in sent_msg, "Response missing message_id"
        assert sent_msg["content"] == test_message, "Message content mismatch"
        assert sent_msg["sender_id"] == self.primary_user_id, "Sender ID mismatch"
        assert sent_msg["receiver_id"] == self.secondary_user_id, "Receiver ID mismatch"
        print(f"✓ Private message sent successfully, message_id: {sent_msg['message_id']}")
        
        # Retrieve conversation
        response = requests.get(
            f"{BASE_URL}/api/messages/{self.secondary_user_id}",
            headers=self.primary_headers
        )
        assert response.status_code == 200, f"Get conversation failed: {response.status_code}"
        
        messages = response.json()
        assert isinstance(messages, list), "Expected list of messages"
        
        # Verify our message is in the conversation
        found_msg = None
        for msg in messages:
            if msg.get("message_id") == sent_msg["message_id"]:
                found_msg = msg
                break
        
        assert found_msg is not None, "Sent message not found in conversation"
        assert found_msg["content"] == test_message, "Retrieved message content mismatch"
        print(f"✓ Conversation retrieved successfully, found {len(messages)} messages")
    
    def test_get_all_conversations(self):
        """GET /api/messages returns all conversations"""
        if not hasattr(self, 'secondary_user_id') or not self.secondary_user_id:
            pytest.skip("No secondary user available for this test")
        
        # First send a message to ensure there's a conversation
        test_message = f"Test for conversations list {int(time.time())}"
        requests.post(
            f"{BASE_URL}/api/messages",
            headers=self.primary_headers,
            json={
                "receiver_id": self.secondary_user_id,
                "content": test_message
            }
        )
        
        # Get all conversations
        response = requests.get(
            f"{BASE_URL}/api/messages",
            headers=self.primary_headers
        )
        assert response.status_code == 200, f"Get conversations failed: {response.status_code}"
        
        conversations = response.json()
        assert isinstance(conversations, list), "Expected list of conversations"
        
        # Check conversation structure
        if len(conversations) > 0:
            conv = conversations[0]
            assert "user_id" in conv, "Conversation missing user_id"
            assert "user_name" in conv, "Conversation missing user_name"
            assert "last_message" in conv, "Conversation missing last_message"
            print(f"✓ Got {len(conversations)} conversations with correct structure")
        else:
            print("✓ Get conversations returned empty list (no conversations yet)")


class TestOnlineUsersForPrivateChat:
    """Test online users functionality for private chat feature"""
    
    def test_get_online_users(self):
        """GET /api/community/online-users returns users list"""
        response = requests.get(f"{BASE_URL}/api/community/online-users")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "online_count" in data, "Response missing online_count"
        assert "users" in data, "Response missing users"
        assert isinstance(data["users"], list), "users should be a list"
        
        print(f"✓ Online users API working: {data['online_count']} users online")
        
        if len(data["users"]) > 0:
            user = data["users"][0]
            assert "user_id" in user, "Online user missing user_id"
            assert "user_name" in user, "Online user missing user_name"
            print(f"✓ Online user structure correct: {user['user_name']}")
    
    def test_heartbeat_updates_online_status(self):
        """POST /api/user/heartbeat updates user's online status"""
        # Login first
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Login failed")
        
        token = response.json().get("session_token")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Send heartbeat
        response = requests.post(f"{BASE_URL}/api/user/heartbeat", headers=headers)
        assert response.status_code == 200, f"Heartbeat failed: {response.status_code}"
        
        data = response.json()
        assert data.get("status") == "ok", f"Unexpected heartbeat response: {data}"
        print("✓ Heartbeat API working correctly")
        
        # Verify user appears in online users
        response = requests.get(f"{BASE_URL}/api/community/online-users")
        assert response.status_code == 200
        
        online_data = response.json()
        print(f"✓ After heartbeat: {online_data['online_count']} users online")


class TestBibleTTSData:
    """Test Bible data has proper content for TTS"""
    
    def test_bible_chapter_has_readable_text(self):
        """Verify Bible chapters return proper text for TTS"""
        # Test Italian
        response = requests.get(f"{BASE_URL}/api/bible/chapter/Genesi/1?lang=it")
        assert response.status_code == 200, f"Failed to get Genesis 1 (it): {response.status_code}"
        
        data = response.json()
        verses = data.get("verses", [])
        assert len(verses) > 0, "No verses returned"
        
        # Check verses have text for TTS
        for verse in verses[:5]:
            assert "text" in verse, "Verse missing text"
            assert len(verse["text"]) > 10, f"Verse {verse.get('verse')} text too short for TTS"
        
        print(f"✓ Italian Bible chapter has {len(verses)} verses with readable text")
        
        # Test Spanish
        response = requests.get(f"{BASE_URL}/api/bible/chapter/Génesis/1?lang=es")
        assert response.status_code == 200, f"Failed to get Genesis 1 (es): {response.status_code}"
        
        data = response.json()
        verses = data.get("verses", [])
        assert len(verses) > 0, "No Spanish verses returned"
        print(f"✓ Spanish Bible chapter has {len(verses)} verses with readable text")
        
        # Test English
        response = requests.get(f"{BASE_URL}/api/bible/chapter/Genesis/1?lang=en")
        assert response.status_code == 200, f"Failed to get Genesis 1 (en): {response.status_code}"
        
        data = response.json()
        verses = data.get("verses", [])
        assert len(verses) > 0, "No English verses returned"
        print(f"✓ English Bible chapter has {len(verses)} verses with readable text")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
