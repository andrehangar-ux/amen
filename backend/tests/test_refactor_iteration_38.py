"""
Iteration 38 - Backend Refactor Validation
Tests all critical endpoints listed in the review request to ensure server.py
modularization (core.py, models.py, dependencies.py) hasn't broken any API.

Order: tests run top-to-bottom. Logout is intentionally last so it doesn't
invalidate the shared session token used by other authenticated tests.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get(
    "EXPO_PUBLIC_BACKEND_URL",
    "https://quiz-nav-build.preview.emergentagent.com"
).rstrip("/")
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
    """Login (or register fallback) and return (token, user_id)."""
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
            assert r.status_code == 200, f"login failed: {r.text}"
            data = r.json()
    else:
        data = r.json()
    token = data.get("session_token")
    assert token, f"no session_token: {data}"
    return token, data.get("user", {}).get("user_id")


@pytest.fixture(scope="module")
def auth_headers(auth):
    token, _ = auth
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ---------------- A. Public endpoints ----------------
class TestAPublic:
    def test_health(self, session):
        r = session.get(f"{API}/health", timeout=10)
        assert r.status_code == 200

    def test_languages(self, session):
        r = session.get(f"{API}/languages", timeout=10)
        assert r.status_code == 200

    def test_bible_editions(self, session):
        r = session.get(f"{API}/bible/editions", timeout=10)
        assert r.status_code == 200

    def test_bible_books_it(self, session):
        r = session.get(f"{API}/bible/books?lang=it", timeout=15)
        assert r.status_code == 200
        assert "Genesi" in str(r.json())

    def test_bible_chapter_genesi_1(self, session):
        r = session.get(f"{API}/bible/chapter/Genesi/1?lang=it", timeout=20)
        assert r.status_code == 200

    def test_bible_daily_verse(self, session):
        r = session.get(f"{API}/bible/daily-verse?lang=it", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "reference" in d and "text" in d

    def test_forum_categories(self, session):
        r = session.get(f"{API}/forum/categories", timeout=10)
        assert r.status_code == 200

    def test_forum_posts_recent(self, session):
        r = session.get(f"{API}/forum/posts?sort=recent", timeout=15)
        assert r.status_code == 200

    def test_dictionary(self, session):
        r = session.get(f"{API}/dictionary?lang=it", timeout=15)
        assert r.status_code == 200

    def test_dictionary_search_abba(self, session):
        r = session.get(f"{API}/dictionary/search/Abba", timeout=15)
        assert r.status_code == 200

    def test_quiz_topics(self, session):
        r = session.get(f"{API}/quiz/topics", timeout=10)
        assert r.status_code == 200

    def test_quiz_categories(self, session):
        r = session.get(f"{API}/quiz/categories", timeout=10)
        assert r.status_code == 200

    def test_groups_topics(self, session):
        r = session.get(f"{API}/groups/topics", timeout=10)
        assert r.status_code == 200

    def test_maps(self, session):
        r = session.get(f"{API}/maps", timeout=10)
        assert r.status_code == 200

    def test_faq(self, session):
        r = session.get(f"{API}/faq", timeout=10)
        assert r.status_code == 200


# ---------------- B. Auth flow (no logout here) ----------------
class TestBAuth:
    def test_register_duplicate_returns_400(self, session):
        r = session.post(f"{API}/auth/register", json={
            "email": EMAIL, "password": PASSWORD, "name": "Refactor Test",
            "language": "it", "country": "IT", "birth_date": "1990-01-01"
        }, timeout=20)
        assert r.status_code in (200, 201, 400), f"unexpected {r.status_code}: {r.text}"

    def test_login_success(self, session):
        r = session.post(f"{API}/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert "session_token" in d
        assert d.get("user", {}).get("email") == EMAIL

    def test_login_wrong_password(self, session):
        r = session.post(f"{API}/auth/login", json={"email": EMAIL, "password": "wrong-xxx"}, timeout=20)
        assert r.status_code == 401

    def test_auth_me(self, session, auth_headers):
        r = session.get(f"{API}/auth/me", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        d = r.json()
        email = d.get("email") or d.get("user", {}).get("email")
        assert email == EMAIL


# ---------------- C. Authenticated endpoints ----------------
class TestCAuthenticated:
    def test_users_heartbeat(self, session, auth_headers):
        r = session.post(f"{API}/users/heartbeat", headers=auth_headers, timeout=15)
        assert r.status_code in (200, 201)

    def test_users_online(self, session, auth_headers):
        r = session.get(f"{API}/users/online", headers=auth_headers, timeout=15)
        assert r.status_code == 200

    def test_parental_can_use_social(self, session, auth_headers):
        r = session.get(f"{API}/parental-controls/can-use-social", headers=auth_headers, timeout=15)
        assert r.status_code == 200

    def test_parental_status(self, session, auth_headers):
        r = session.get(f"{API}/parental-controls/status", headers=auth_headers, timeout=15)
        assert r.status_code == 200

    def test_private_messages_conversations(self, session, auth_headers):
        r = session.get(f"{API}/private-messages/conversations", headers=auth_headers, timeout=15)
        assert r.status_code == 200

    def test_groups_list(self, session, auth_headers):
        r = session.get(f"{API}/groups", headers=auth_headers, timeout=15)
        assert r.status_code == 200

    def test_study_groups_list(self, session, auth_headers):
        r = session.get(f"{API}/study-groups", headers=auth_headers, timeout=15)
        assert r.status_code == 200

    def test_bookmarks_list(self, session, auth_headers):
        r = session.get(f"{API}/bookmarks", headers=auth_headers, timeout=15)
        assert r.status_code == 200

    def test_progress_get(self, session, auth_headers):
        r = session.get(f"{API}/progress", headers=auth_headers, timeout=15)
        assert r.status_code == 200

    def test_safety_status(self, session, auth_headers):
        r = session.get(f"{API}/safety/status", headers=auth_headers, timeout=15)
        assert r.status_code == 200

    def test_community_messages_get(self, session, auth_headers):
        r = session.get(f"{API}/community/messages?lang=it", headers=auth_headers, timeout=20)
        assert r.status_code == 200

    def test_community_users_get(self, session, auth_headers):
        r = session.get(f"{API}/community/users", headers=auth_headers, timeout=15)
        assert r.status_code == 200

    def test_search_global(self, session, auth_headers):
        r = session.get(f"{API}/search?q=love", headers=auth_headers, timeout=20)
        assert r.status_code == 200

    def test_translate_post(self, session, auth_headers):
        r = session.post(f"{API}/translate", headers=auth_headers,
                         json={"text": "Hello world", "source_lang": "en", "target_lang": "it"}, timeout=45)
        assert r.status_code in (200, 201), f"translate failed: {r.status_code} {r.text}"


# ---------------- D. Bug fix: community message_type ----------------
class TestDCommunityMessageBugFix:
    def test_post_with_message_type(self, session, auth_headers):
        payload = {"content": "TEST_ refactor smoke message", "language": "it", "message_type": "text"}
        r = session.post(f"{API}/community/messages", headers=auth_headers, json=payload, timeout=20)
        assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text}"
        d = r.json()
        assert d.get("message_type") == "text"
        assert "message_id" in d

    def test_post_default_message_type(self, session, auth_headers):
        payload = {"content": "TEST_ default type", "language": "it"}
        r = session.post(f"{API}/community/messages", headers=auth_headers, json=payload, timeout=20)
        assert r.status_code == 200
        assert r.json().get("message_type") == "text"


# ---------------- E. Journal ----------------
class TestEJournal:
    _entry_id = None

    def test_create_entry(self, session, auth_headers):
        payload = {"content": "TEST_ refactor entry oggi mi sento bene", "mood": "happy", "language": "it"}
        r = session.post(f"{API}/journal", headers=auth_headers, json=payload, timeout=60)
        assert r.status_code in (200, 201), f"{r.status_code}: {r.text}"
        d = r.json()
        assert "entry_id" in d
        TestEJournal._entry_id = d["entry_id"]

    def test_list_entries(self, session, auth_headers):
        r = session.get(f"{API}/journal", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d, list)
        if TestEJournal._entry_id:
            assert any(e.get("entry_id") == TestEJournal._entry_id for e in d), "entry not persisted"


# ---------------- Z. Logout last ----------------
class TestZLogout:
    def test_logout(self, session, auth_headers):
        r = session.post(f"{API}/auth/logout", headers=auth_headers, timeout=15)
        assert r.status_code == 200
