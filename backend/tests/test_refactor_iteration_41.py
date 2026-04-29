"""
Iteration 41 - Backend Refactor Phase 2 Continuation Regression
Validates the 4 NEWLY-extracted route modules + regression of previously-extracted
modules (iter 40) and endpoints that REMAIN in server.py.

New modules being validated (iter 41 priority):
- routes/legal_donations.py    (consent, policy, donations)
- routes/community.py          (community messages, translate, like, users)
- routes/private_messages.py   (1-on-1 chat + legacy /messages routes)
- routes/users_presence.py     (heartbeat, online, offline, settings)

Regression of iter-40 modules:
- routes/auth.py, notifications_friends.py, journal_bookmarks_progress.py,
  forum.py, parental_safety.py

Regression of endpoints still in server.py:
- health, languages, bible (editions/books/chapter/daily-verse), quiz topics+categories,
  dictionary, groups, study-groups, maps, faq, worship, radios, feelings/analyze.

Auth: Bearer token (Authorization header), per main agent guidance to
avoid cookie-based false positives from earlier iterations.
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "https://quiz-nav-build.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

EMAIL = "refactortest@amen.com"
PASSWORD = "Test1234!"


# ---------------- Fixtures ----------------
@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def auth(session):
    """Login (or register-then-login) and return (session_token, user_id)."""
    r = session.post(f"{API}/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=20)
    if r.status_code != 200:
        reg = session.post(f"{API}/auth/register", json={
            "email": EMAIL, "password": PASSWORD, "name": "Refactor Test",
            "language": "it", "country": "IT", "birth_date": "1990-01-01"
        }, timeout=20)
        if reg.status_code in (200, 201):
            data = reg.json()
        else:
            r = session.post(f"{API}/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=20)
            assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
            data = r.json()
    else:
        data = r.json()
    token = data.get("session_token")
    assert token, f"no session_token: {data}"
    return token, data.get("user", {}).get("user_id")


@pytest.fixture(scope="module")
def H(auth):
    """Authorization header dict (Bearer token)."""
    token, _ = auth
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def UID(auth):
    _, user_id = auth
    return user_id


# ============================================================================
# legal_donations.py
# ============================================================================
class TestLegalDonations:
    def test_consent_status(self, H):
        r = requests.get(f"{API}/consent/status", headers=H, timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert "accepted" in body
        assert isinstance(body["accepted"], bool)

    def test_consent_accept_v1(self, H):
        r = requests.post(f"{API}/consent/accept?version=1", headers=H, timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert body.get("success") is True
        assert body.get("version") == "1"
        assert "document_hash" in body and len(body["document_hash"]) == 64
        assert "timestamp" in body

    def test_consent_status_after_accept(self, H):
        # GET-after-POST verification that consent persisted
        r = requests.get(f"{API}/consent/status", headers=H, timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert body.get("accepted") is True
        assert body.get("version") == "1"

    def test_consent_requires_auth(self):
        r = requests.post(f"{API}/consent/accept?version=1", timeout=15)
        assert r.status_code == 401

    def test_donations_config(self):
        # public endpoint
        r = requests.get(f"{API}/donations/config", timeout=15)
        assert r.status_code == 200
        body = r.json()
        for k in ("paypal_email", "paypal_link", "iban", "intestatario", "banca", "bic_swift"):
            assert k in body, f"missing key {k}"
        assert body["paypal_email"] == "andrehangar@live.it"

    def test_donations_create_paypal_and_persist(self, H):
        payload = {"amount": 5.0, "method": "paypal", "message": "TEST_iter41 paypal"}
        r = requests.post(f"{API}/donations", headers=H, json=payload, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["amount"] == 5.0
        assert body["method"] == "paypal"
        assert body["status"] == "completed"
        assert "donation_id" in body
        assert body["paypal_email"] == "andrehangar@live.it"
        donation_id = body["donation_id"]

        # GET to verify persistence
        r2 = requests.get(f"{API}/donations", headers=H, timeout=15)
        assert r2.status_code == 200
        donations = r2.json()
        assert any(d["donation_id"] == donation_id for d in donations)

    def test_donations_create_bonifico_includes_bank_details(self, H):
        payload = {"amount": 10.0, "method": "bonifico", "message": "TEST_iter41 bonifico"}
        r = requests.post(f"{API}/donations", headers=H, json=payload, timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "pending"
        assert "bank_details" in body
        assert body["bank_details"]["iban"].startswith("IT46")
        assert "causale" in body["bank_details"]

    def test_donations_requires_auth(self):
        r = requests.get(f"{API}/donations", timeout=15)
        assert r.status_code == 401

    def test_policy_check_clean(self):
        r = requests.get(f"{API}/policy/check", params={"content": "hello"}, timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert body.get("status") == "ok"
        assert body.get("content_cleared") is True

    def test_policy_check_violation(self):
        r = requests.get(f"{API}/policy/check", params={"content": "I want to reverse engineer this"}, timeout=15)
        assert r.status_code == 403
        detail = r.json().get("detail", {})
        assert detail.get("error_code") == "POLICY_VIOLATION_403"


# ============================================================================
# community.py
# ============================================================================
class TestCommunity:
    @pytest.fixture(scope="class")
    def created_message(self, H):
        payload = {"content": "TEST_iter41 community ciao mondo", "language": "it", "message_type": "text"}
        r = requests.post(f"{API}/community/messages", headers=H, json=payload, timeout=20)
        assert r.status_code == 200, r.text
        msg = r.json()
        assert msg["content"] == payload["content"]
        assert msg["original_language"] == "it"
        assert msg["message_type"] == "text"
        assert msg["likes"] == 0
        assert "message_id" in msg
        return msg

    def test_create_message(self, created_message):
        assert created_message["message_id"]

    def test_get_messages(self, H, created_message):
        r = requests.get(f"{API}/community/messages", headers=H, params={"lang": "it"}, timeout=20)
        assert r.status_code == 200
        msgs = r.json()
        assert isinstance(msgs, list)
        ids = [m["message_id"] for m in msgs]
        assert created_message["message_id"] in ids
        # The message returned in the list should have translated_content because of the lang param
        match = next(m for m in msgs if m["message_id"] == created_message["message_id"])
        assert "translated_content" in match

    def test_translate_message_same_language(self, created_message):
        # public endpoint (no auth) per request
        mid = created_message["message_id"]
        r = requests.post(f"{API}/community/messages/{mid}/translate", params={"target_lang": "it"}, timeout=20)
        assert r.status_code == 200
        body = r.json()
        assert body["is_original"] is True
        assert body["translated_text"] == created_message["content"]

    def test_translate_message_different_language(self, created_message):
        mid = created_message["message_id"]
        r = requests.post(f"{API}/community/messages/{mid}/translate", params={"target_lang": "en"}, timeout=30)
        assert r.status_code == 200
        body = r.json()
        # translated_text should exist; is_original should be False
        assert "translated_text" in body
        assert body.get("is_original") in (False, None) or body["is_original"] is False

    def test_translate_unknown_message(self):
        r = requests.post(f"{API}/community/messages/{uuid.uuid4()}/translate", params={"target_lang": "en"}, timeout=15)
        assert r.status_code == 404

    def test_like_message_and_unknown(self, H, created_message):
        mid = created_message["message_id"]
        r = requests.post(f"{API}/community/messages/{mid}/like", headers=H, timeout=15)
        assert r.status_code == 200
        assert r.json().get("success") is True

        r2 = requests.post(f"{API}/community/messages/{uuid.uuid4()}/like", headers=H, timeout=15)
        assert r2.status_code == 404

    def test_get_users(self, H, UID):
        r = requests.get(f"{API}/community/users", headers=H, timeout=15)
        assert r.status_code == 200
        users = r.json()
        assert isinstance(users, list)
        # Self should NOT appear in the list
        assert all(u["user_id"] != UID for u in users)
        # Each entry has expected shape
        for u in users[:5]:
            assert "user_id" in u and "name" in u and "is_online" in u

    def test_community_requires_auth(self):
        r = requests.get(f"{API}/community/messages", timeout=15)
        assert r.status_code == 401
        r2 = requests.post(f"{API}/community/messages", json={"content": "x", "language": "it"}, timeout=15)
        assert r2.status_code == 401


# ============================================================================
# private_messages.py  (new /private-messages + legacy /messages)
# ============================================================================
@pytest.fixture(scope="module")
def second_user(session):
    """Register or reuse a second user for private-message tests."""
    email = "refactortest2@amen.com"
    pwd = "Test1234!"
    s2 = requests.Session()
    r = s2.post(f"{API}/auth/login", json={"email": email, "password": pwd}, timeout=20)
    if r.status_code != 200:
        reg = s2.post(f"{API}/auth/register", json={
            "email": email, "password": pwd, "name": "Refactor Test 2",
            "language": "it", "country": "IT", "birth_date": "1990-05-05"
        }, timeout=20)
        if reg.status_code in (200, 201):
            data = reg.json()
        else:
            r = s2.post(f"{API}/auth/login", json={"email": email, "password": pwd}, timeout=20)
            assert r.status_code == 200, reg.text
            data = r.json()
    else:
        data = r.json()
    return {
        "token": data.get("session_token"),
        "user_id": data.get("user", {}).get("user_id"),
        "name": data.get("user", {}).get("name"),
    }


class TestPrivateMessages:
    def test_send_private_message(self, H, second_user):
        payload = {"receiver_id": second_user["user_id"], "content": "TEST_iter41 private hi"}
        r = requests.post(f"{API}/private-messages", headers=H, json=payload, timeout=15)
        assert r.status_code == 200, r.text
        msg = r.json()
        assert msg["receiver_id"] == second_user["user_id"]
        assert msg["content"] == payload["content"]
        assert msg["read"] is False
        assert "conversation_id" in msg
        assert "message_id" in msg

    def test_get_conversations(self, H, second_user):
        r = requests.get(f"{API}/private-messages/conversations", headers=H, timeout=15)
        assert r.status_code == 200
        convos = r.json()
        assert isinstance(convos, list)
        assert any(c["other_user_id"] == second_user["user_id"] for c in convos)

    def test_get_messages_with_user(self, H, second_user):
        r = requests.get(f"{API}/private-messages/{second_user['user_id']}", headers=H, timeout=15)
        assert r.status_code == 200
        msgs = r.json()
        assert isinstance(msgs, list)
        assert len(msgs) >= 1
        # Latest message should be the one we just sent
        assert any(m["content"] == "TEST_iter41 private hi" for m in msgs)

    def test_send_to_unknown_user(self, H):
        payload = {"receiver_id": "user_does_not_exist_xyz", "content": "x"}
        r = requests.post(f"{API}/private-messages", headers=H, json=payload, timeout=15)
        assert r.status_code == 404

    def test_legacy_send_message(self, H, second_user):
        payload = {"receiver_id": second_user["user_id"], "content": "TEST_iter41 legacy hello"}
        r = requests.post(f"{API}/messages", headers=H, json=payload, timeout=15)
        assert r.status_code == 200, r.text
        msg = r.json()
        # Legacy uses is_read field, no conversation_id
        assert msg["receiver_id"] == second_user["user_id"]
        assert msg["is_read"] is False
        assert msg["content"] == payload["content"]
        assert "conversation_id" not in msg

    def test_legacy_get_messages_list(self, H, second_user):
        r = requests.get(f"{API}/messages", headers=H, timeout=15)
        assert r.status_code == 200
        convs = r.json()
        assert isinstance(convs, list)
        assert any(c["user_id"] == second_user["user_id"] for c in convs)
        # entry shape
        match = next(c for c in convs if c["user_id"] == second_user["user_id"])
        assert "user_name" in match
        assert "last_message" in match
        assert "unread_count" in match

    def test_legacy_get_conversation(self, H, second_user):
        r = requests.get(f"{API}/messages/{second_user['user_id']}", headers=H, timeout=15)
        assert r.status_code == 200
        msgs = r.json()
        assert isinstance(msgs, list)
        assert len(msgs) >= 1

    def test_legacy_creates_notification_for_receiver(self, H, second_user):
        # Send from primary -> second_user, then check second_user notifications has it
        unique = f"TEST_iter41 notify {uuid.uuid4().hex[:6]}"
        r = requests.post(
            f"{API}/messages",
            headers=H,
            json={"receiver_id": second_user["user_id"], "content": unique},
            timeout=15,
        )
        assert r.status_code == 200
        # check receiver's notifications list
        H2 = {"Authorization": f"Bearer {second_user['token']}", "Content-Type": "application/json"}
        n = requests.get(f"{API}/notifications", headers=H2, timeout=15)
        assert n.status_code == 200
        notifs = n.json()
        assert any(x.get("notification_type") == "message" for x in notifs), \
            "Expected a 'message' notification for receiver after legacy /messages POST"

    def test_private_messages_requires_auth(self):
        r = requests.get(f"{API}/private-messages/conversations", timeout=15)
        assert r.status_code == 401
        r2 = requests.get(f"{API}/messages", timeout=15)
        assert r2.status_code == 401


# ============================================================================
# users_presence.py
# ============================================================================
class TestUsersPresence:
    def test_heartbeat(self, H):
        r = requests.post(f"{API}/users/heartbeat", headers=H, timeout=15)
        assert r.status_code == 200
        assert r.json().get("status") == "ok"

    def test_online_users_includes_self(self, H, UID):
        r = requests.get(f"{API}/users/online", headers=H, timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert "online_count" in body
        assert "users" in body
        assert isinstance(body["users"], list)
        assert any(u["user_id"] == UID for u in body["users"]), \
            "Self should appear online after heartbeat"

    def test_offline(self, H):
        r = requests.post(f"{API}/users/offline", headers=H, timeout=15)
        assert r.status_code == 200
        assert r.json().get("status") == "offline"

    def test_update_settings(self, H):
        r = requests.put(f"{API}/users/settings", headers=H, json={"language": "it"}, timeout=15)
        assert r.status_code == 200
        body = r.json()
        # should not leak password_hash or _id
        assert "password_hash" not in body
        assert "_id" not in body
        assert body.get("language") == "it"

    def test_update_settings_ignores_unknown_fields(self, H):
        r = requests.put(f"{API}/users/settings", headers=H,
                         json={"language": "it", "is_admin": True, "balance": 99999}, timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert body.get("is_admin") is not True
        assert body.get("balance") != 99999

    def test_presence_requires_auth(self):
        r = requests.post(f"{API}/users/heartbeat", timeout=15)
        assert r.status_code == 401
        r2 = requests.get(f"{API}/users/online", timeout=15)
        assert r2.status_code == 401
        r3 = requests.put(f"{API}/users/settings", json={"language": "it"}, timeout=15)
        assert r3.status_code == 401


# ============================================================================
# REGRESSION - previously extracted modules (iter 39/40)
# ============================================================================
class TestPreviousModulesRegression:
    def test_auth_me(self, H):
        r = requests.get(f"{API}/auth/me", headers=H, timeout=15)
        assert r.status_code == 200
        assert "user_id" in r.json()

    def test_notifications(self, H):
        r = requests.get(f"{API}/notifications", headers=H, timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_friends(self, H):
        r = requests.get(f"{API}/friends", headers=H, timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_journal(self, H):
        r = requests.get(f"{API}/journal", headers=H, timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_bookmarks(self, H):
        r = requests.get(f"{API}/bookmarks", headers=H, timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_progress(self, H):
        r = requests.get(f"{API}/progress", headers=H, timeout=15)
        assert r.status_code == 200
        # progress is a dict (stats)
        assert isinstance(r.json(), (dict, list))

    def test_forum_categories(self):
        r = requests.get(f"{API}/forum/categories", timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_forum_posts(self):
        r = requests.get(f"{API}/forum/posts", timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_safety_status(self, H):
        r = requests.get(f"{API}/safety/status", headers=H, timeout=15)
        assert r.status_code == 200

    def test_parental_controls_status(self, H):
        r = requests.get(f"{API}/parental-controls/status", headers=H, timeout=15)
        assert r.status_code == 200


# ============================================================================
# REGRESSION - endpoints that REMAIN in server.py
# ============================================================================
class TestServerPyRegression:
    def test_health(self):
        r = requests.get(f"{API}/health", timeout=15)
        assert r.status_code == 200

    def test_languages(self):
        r = requests.get(f"{API}/languages", timeout=15)
        assert r.status_code == 200
        body = r.json()
        # API returns a dict keyed by language code (e.g. {"en": {...}, "it": {...}})
        assert isinstance(body, dict)
        assert "it" in body and "en" in body

    def test_bible_editions(self):
        r = requests.get(f"{API}/bible/editions", timeout=15)
        assert r.status_code == 200

    def test_bible_books(self):
        r = requests.get(f"{API}/bible/books", params={"lang": "it"}, timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, (list, dict))

    def test_bible_chapter(self):
        r = requests.get(f"{API}/bible/chapter/Genesi/1", timeout=15)
        assert r.status_code == 200

    def test_daily_verse(self):
        r = requests.get(f"{API}/bible/daily-verse", params={"lang": "it"}, timeout=20)
        assert r.status_code == 200

    def test_quiz_topics(self):
        r = requests.get(f"{API}/quiz/topics", timeout=15)
        assert r.status_code == 200

    def test_quiz_categories(self):
        r = requests.get(f"{API}/quiz/categories", timeout=15)
        assert r.status_code == 200

    def test_dictionary(self):
        r = requests.get(f"{API}/dictionary", params={"lang": "it"}, timeout=15)
        assert r.status_code == 200

    def test_dictionary_search(self):
        r = requests.get(f"{API}/dictionary/search/Abba", timeout=15)
        assert r.status_code == 200

    def test_groups(self, H):
        # /groups requires auth
        r = requests.get(f"{API}/groups", headers=H, timeout=15)
        assert r.status_code == 200

    def test_groups_topics(self):
        r = requests.get(f"{API}/groups/topics", timeout=15)
        assert r.status_code == 200

    def test_study_groups(self, H):
        r = requests.get(f"{API}/study-groups", headers=H, timeout=15)
        assert r.status_code == 200

    def test_maps(self):
        r = requests.get(f"{API}/maps", timeout=15)
        assert r.status_code == 200

    def test_maps_palestine(self):
        r = requests.get(f"{API}/maps/palestine", timeout=15)
        assert r.status_code == 200

    def test_faq(self):
        r = requests.get(f"{API}/faq", timeout=15)
        assert r.status_code == 200

    def test_worship(self):
        r = requests.get(f"{API}/worship", timeout=15)
        assert r.status_code == 200

    def test_radios(self):
        r = requests.get(f"{API}/radios", timeout=15)
        assert r.status_code == 200

    def test_feelings_analyze(self, H):
        # FeelingRequest model expects 'text' field
        r = requests.post(
            f"{API}/feelings/analyze",
            headers=H,
            json={"text": "Mi sento gioioso oggi", "language": "it"},
            timeout=60,
        )
        assert r.status_code == 200, f"feelings/analyze failed: {r.status_code} {r.text[:300]}"
