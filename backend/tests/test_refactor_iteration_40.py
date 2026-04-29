"""
Iteration 40 - Backend Refactor Phase 2 Regression
Validates the 4 newly-extracted route modules + regression of legacy server.py endpoints.

Modules being validated:
- routes/notifications_friends.py (8 endpoints)
- routes/journal_bookmarks_progress.py (10 endpoints)
- routes/forum.py (7 endpoints)
- routes/parental_safety.py (10 endpoints)
- routes/auth.py (already validated in iter 39, light spot-check here)
- Regression for endpoints still in server.py

Auth: Bearer token (per main agent guidance to avoid prior false positives w/ cookies).
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
    token, _ = auth
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ============================================================
# A. NOTIFICATIONS + FRIENDS  (routes/notifications_friends.py)
# ============================================================
class TestANotificationsFriends:
    def test_get_notifications(self, session, H):
        r = session.get(f"{API}/notifications", headers=H, timeout=15)
        assert r.status_code == 200, f"{r.status_code}: {r.text}"
        assert isinstance(r.json(), list)

    def test_unread_count(self, session, H):
        r = session.get(f"{API}/notifications/unread-count", headers=H, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "count" in d
        assert isinstance(d["count"], int)

    def test_notifications_require_auth(self):
        # Use a fresh session to avoid shared login cookies
        r = requests.get(f"{API}/notifications", timeout=15)
        assert r.status_code in (401, 403), f"{r.status_code}: {r.text}"

    def test_mark_notification_read_idempotent(self, session, H):
        """Even with non-existent notification id, endpoint should return success (update_one no-op)."""
        r = session.post(f"{API}/notifications/nonexistent_id_xyz/read", headers=H, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json().get("success") is True

    def test_read_all(self, session, H):
        r = session.post(f"{API}/notifications/read-all", headers=H, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json().get("success") is True

    def test_get_friends(self, session, H):
        r = session.get(f"{API}/friends", headers=H, timeout=15)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_add_friend_self_returns_400(self, session, H, auth):
        _, my_id = auth
        if not my_id:
            pytest.skip("no user_id")
        r = session.post(f"{API}/friends", headers=H, json={"friend_id": my_id}, timeout=15)
        assert r.status_code == 400, f"{r.status_code}: {r.text}"

    def test_add_friend_unknown_returns_404(self, session, H):
        r = session.post(f"{API}/friends", headers=H,
                         json={"friend_id": f"nonexistent_{uuid.uuid4().hex[:8]}"}, timeout=15)
        assert r.status_code == 404, f"{r.status_code}: {r.text}"

    def test_remove_friend_unknown_returns_404(self, session, H):
        r = session.delete(f"{API}/friends/unknown_friend_xyz", headers=H, timeout=15)
        assert r.status_code == 404, f"{r.status_code}: {r.text}"

    def test_check_friendship(self, session, H, auth):
        _, my_id = auth
        target = my_id or "anyone"
        r = session.get(f"{API}/friends/check/{target}", headers=H, timeout=15)
        assert r.status_code == 200, r.text
        assert "is_friend" in r.json()


# ============================================================
# B. JOURNAL + BOOKMARKS + PROGRESS
# ============================================================
class TestBJournalBookmarksProgress:
    _bookmark_id = None
    _journal_id = None

    def test_create_bookmark(self, session, H):
        payload = {
            "book": "Genesi", "chapter": 1, "verse": 1,
            "text": "TEST_ in principio", "note": "TEST_iter40",
            "highlight_color": "#D4A574"
        }
        r = session.post(f"{API}/bookmarks", headers=H, json=payload, timeout=15)
        assert r.status_code == 200, f"{r.status_code}: {r.text}"
        d = r.json()
        assert d["book"] == "Genesi"
        assert d["chapter"] == 1
        assert "bookmark_id" in d
        TestBJournalBookmarksProgress._bookmark_id = d["bookmark_id"]

    def test_list_bookmarks_includes_created(self, session, H):
        r = session.get(f"{API}/bookmarks", headers=H, timeout=15)
        assert r.status_code == 200, r.text
        ids = [b["bookmark_id"] for b in r.json()]
        assert TestBJournalBookmarksProgress._bookmark_id in ids, "bookmark not persisted"

    def test_delete_bookmark(self, session, H):
        bid = TestBJournalBookmarksProgress._bookmark_id
        if not bid:
            pytest.skip("no bookmark")
        r = session.delete(f"{API}/bookmarks/{bid}", headers=H, timeout=15)
        assert r.status_code == 200, r.text
        # GET should no longer contain it
        r2 = session.get(f"{API}/bookmarks", headers=H, timeout=15)
        assert bid not in [b["bookmark_id"] for b in r2.json()]

    def test_delete_bookmark_not_found(self, session, H):
        r = session.delete(f"{API}/bookmarks/nonexistent_xyz", headers=H, timeout=15)
        assert r.status_code == 404

    def test_create_journal_entry(self, session, H):
        # AI insight is wrapped in try/except; even if AI fails, entry should be saved.
        payload = {"content": "TEST_ iter40 journal entry", "mood": "grato", "language": "it"}
        r = session.post(f"{API}/journal", headers=H, json=payload, timeout=60)
        assert r.status_code == 200, f"{r.status_code}: {r.text}"
        d = r.json()
        assert d["content"] == payload["content"]
        assert d["mood"] == "grato"
        assert "entry_id" in d
        TestBJournalBookmarksProgress._journal_id = d["entry_id"]

    def test_list_journal_entries(self, session, H):
        r = session.get(f"{API}/journal", headers=H, timeout=15)
        assert r.status_code == 200, r.text
        ids = [e["entry_id"] for e in r.json()]
        assert TestBJournalBookmarksProgress._journal_id in ids

    def test_delete_journal_entry(self, session, H):
        eid = TestBJournalBookmarksProgress._journal_id
        if not eid:
            pytest.skip("no journal")
        r = session.delete(f"{API}/journal/{eid}", headers=H, timeout=15)
        assert r.status_code == 200, r.text

    def test_delete_journal_not_found(self, session, H):
        r = session.delete(f"{API}/journal/nonexistent_xyz", headers=H, timeout=15)
        assert r.status_code == 404

    def test_get_progress(self, session, H):
        r = session.get(f"{API}/progress", headers=H, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "reading_streak" in d
        assert "total_chapters_read" in d

    def test_post_reading_progress(self, session, H):
        r = session.post(f"{API}/progress/reading", headers=H, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "reading_streak" in d

    def test_save_chapter_reading(self, session, H):
        r = session.post(f"{API}/progress/reading/chapter?book=Genesi&chapter=1",
                         headers=H, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("success") is True
        assert d.get("book") == "Genesi"
        assert d.get("chapter") == 1

    def test_get_reading_history(self, session, H):
        r = session.get(f"{API}/progress/reading/history?limit=10", headers=H, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "history" in d and "total" in d
        assert isinstance(d["history"], list)


# ============================================================
# C. FORUM (routes/forum.py)
# ============================================================
class TestCForum:
    _post_id = None

    def test_get_categories(self, session):
        r = session.get(f"{API}/forum/categories", timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d, list)
        cat_ids = {c["id"] for c in d}
        assert {"discussion", "prayer", "testimony", "question", "study"}.issubset(cat_ids)

    def test_get_posts_public(self, session):
        r = session.get(f"{API}/forum/posts?limit=5", timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_forum_post(self, session, H):
        payload = {
            "title": f"TEST_ iter40 {uuid.uuid4().hex[:6]}",
            "content": "TEST_ contenuto regression",
            "category": "discussion",
            "tags": ["test", "iter40"],
        }
        r = session.post(f"{API}/forum/posts", headers=H, json=payload, timeout=15)
        assert r.status_code == 200, f"{r.status_code}: {r.text}"
        d = r.json()
        assert "post_id" in d
        assert d["title"] == payload["title"]
        TestCForum._post_id = d["post_id"]

    def test_get_single_post_with_replies(self, session):
        pid = TestCForum._post_id
        if not pid:
            pytest.skip("no post")
        r = session.get(f"{API}/forum/posts/{pid}", timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["post_id"] == pid
        assert "replies" in d and isinstance(d["replies"], list)

    def test_get_post_not_found(self, session):
        r = session.get(f"{API}/forum/posts/nonexistent_xyz", timeout=10)
        assert r.status_code == 404

    def test_vote_forum_post_toggle(self, session, H):
        pid = TestCForum._post_id
        if not pid:
            pytest.skip("no post")
        r1 = session.post(f"{API}/forum/posts/{pid}/vote", headers=H, timeout=15)
        assert r1.status_code == 200, r1.text
        d1 = r1.json()
        assert d1.get("voted") is True
        # Second click toggles off
        r2 = session.post(f"{API}/forum/posts/{pid}/vote", headers=H, timeout=15)
        assert r2.status_code == 200
        assert r2.json().get("voted") is False

    def test_reply_forum_post(self, session, H):
        pid = TestCForum._post_id
        if not pid:
            pytest.skip("no post")
        r = session.post(f"{API}/forum/posts/{pid}/reply", headers=H,
                         json={"content": "TEST_ iter40 reply"}, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "reply_id" in d
        assert d["content"] == "TEST_ iter40 reply"

    def test_create_post_requires_auth(self):
        # Use fresh requests (no shared cookies)
        r = requests.post(f"{API}/forum/posts",
                          json={"title": "x", "content": "y", "category": "discussion"},
                          timeout=15)
        assert r.status_code in (401, 403)


# ============================================================
# D. PARENTAL + SAFETY (routes/parental_safety.py)
# ============================================================
class TestDParentalSafety:
    def test_safety_status(self, session, H):
        r = session.get(f"{API}/safety/status", headers=H, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("is_minor", "age", "parental_consent"):
            assert k in d
        # refactortest@amen.com is adult (1990-01-01)
        assert d["is_minor"] is False

    def test_acknowledge_reminder(self, session, H):
        r = session.post(f"{API}/safety/acknowledge-reminder", headers=H, timeout=15)
        assert r.status_code == 200
        assert r.json().get("success") is True

    def test_can_share_info_adult(self, session, H):
        r = session.get(f"{API}/safety/can-share-info", headers=H, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d.get("can_share") is True
        assert d.get("reason") == "adult"

    def test_parental_controls_status(self, session, H):
        r = session.get(f"{API}/parental-controls/status", headers=H, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "is_minor" in d
        assert "parent_pin_set" in d

    def test_set_pin_invalid_length(self, session, H):
        r = session.post(f"{API}/parental-controls/set-pin", headers=H,
                         json={"new_pin": "12"}, timeout=15)
        assert r.status_code == 400, r.text

    def test_set_pin_non_numeric(self, session, H):
        r = session.post(f"{API}/parental-controls/set-pin", headers=H,
                         json={"new_pin": "abcd"}, timeout=15)
        assert r.status_code == 400

    def test_set_and_verify_pin(self, session, H):
        # Set valid PIN
        r1 = session.post(f"{API}/parental-controls/set-pin", headers=H,
                          json={"new_pin": "4242"}, timeout=15)
        assert r1.status_code == 200, r1.text
        # Verify correct PIN
        r2 = session.post(f"{API}/parental-controls/verify-pin?pin=4242", headers=H, timeout=15)
        assert r2.status_code == 200, r2.text
        assert r2.json().get("verified") is True
        # Verify wrong PIN
        r3 = session.post(f"{API}/parental-controls/verify-pin?pin=9999", headers=H, timeout=15)
        assert r3.status_code == 403

    def test_update_parental_controls(self, session, H):
        payload = {
            "parent_pin": "4242",
            "social_features_enabled": True,
            "social_level": "friends_only",
            "media_sharing_enabled": False
        }
        r = session.put(f"{API}/parental-controls/update", headers=H, json=payload, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json().get("success") is True

    def test_update_parental_controls_wrong_pin(self, session, H):
        r = session.put(f"{API}/parental-controls/update", headers=H,
                        json={"parent_pin": "0000"}, timeout=15)
        assert r.status_code == 403

    def test_can_use_social_adult(self, session, H):
        r = session.get(f"{API}/parental-controls/can-use-social", headers=H, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d.get("can_use_social") is True
        assert d.get("reason") == "adult"

    def test_set_birth_date_valid(self, session, H):
        # Keep adult birth date so other tests stay consistent
        r = session.put(f"{API}/users/birth-date?birth_date=1990-01-01", headers=H, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json().get("is_minor") is False

    def test_set_birth_date_invalid_format(self, session, H):
        r = session.put(f"{API}/users/birth-date?birth_date=01-01-1990", headers=H, timeout=15)
        # FastAPI Query regex returns 422 (validation), our handler also handles 400.
        assert r.status_code in (400, 422), r.text

    def test_parental_consent_set_code(self, session, H):
        r = session.post(f"{API}/safety/parental-consent", headers=H,
                         json={"consent_code": "TEST1234", "consent_given": True}, timeout=15)
        assert r.status_code == 200, r.text


# ============================================================
# E. AUTH spot-check (already validated iter 39)
# ============================================================
class TestEAuthSpotCheck:
    def test_auth_me(self, session, H):
        r = session.get(f"{API}/auth/me", headers=H, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        email = d.get("email") or d.get("user", {}).get("email")
        assert email == EMAIL


# ============================================================
# F. REGRESSION - endpoints that REMAIN in server.py
# ============================================================
class TestFRegressionServerPy:
    def test_health(self, session):
        r = session.get(f"{API}/health", timeout=10)
        assert r.status_code == 200

    def test_languages(self, session):
        r = session.get(f"{API}/languages", timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))

    def test_bible_editions(self, session):
        r = session.get(f"{API}/bible/editions", timeout=10)
        assert r.status_code == 200

    def test_bible_books(self, session):
        r = session.get(f"{API}/bible/books", timeout=10)
        assert r.status_code == 200

    def test_bible_chapter_genesi_1(self, session):
        r = session.get(f"{API}/bible/chapter/Genesi/1", timeout=15)
        assert r.status_code == 200, r.text

    def test_daily_verse(self, session):
        r = session.get(f"{API}/bible/daily-verse?lang=it", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "reference" in d and "text" in d

    def test_community_post_message(self, session, H):
        payload = {"content": "TEST_ iter40 community", "language": "it", "message_type": "text"}
        r = session.post(f"{API}/community/messages", headers=H, json=payload, timeout=20)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("message_type") == "text"
        assert "message_id" in d

    def test_community_get_messages(self, session):
        r = session.get(f"{API}/community/messages?limit=5", timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_community_users(self, session):
        r = session.get(f"{API}/community/users", timeout=10)
        assert r.status_code == 200

    def test_users_heartbeat(self, session, H):
        r = session.post(f"{API}/users/heartbeat", headers=H, timeout=10)
        assert r.status_code == 200

    def test_users_online(self, session):
        r = session.get(f"{API}/users/online", timeout=10)
        assert r.status_code == 200

    def test_private_messages_conversations(self, session, H):
        r = session.get(f"{API}/private-messages/conversations", headers=H, timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_quiz_topics(self, session):
        r = session.get(f"{API}/quiz/topics", timeout=10)
        assert r.status_code == 200

    def test_quiz_categories(self, session):
        r = session.get(f"{API}/quiz/categories", timeout=10)
        assert r.status_code == 200

    def test_dictionary(self, session):
        r = session.get(f"{API}/dictionary?lang=it", timeout=15)
        assert r.status_code == 200

    def test_dictionary_search_abba(self, session):
        r = session.get(f"{API}/dictionary/search/Abba", timeout=15)
        assert r.status_code == 200

    def test_groups_topics(self, session):
        r = session.get(f"{API}/groups/topics", timeout=10)
        assert r.status_code == 200

    def test_groups_list(self, session):
        r = session.get(f"{API}/groups", timeout=10)
        assert r.status_code == 200

    def test_study_groups(self, session):
        r = session.get(f"{API}/study-groups", timeout=10)
        assert r.status_code == 200

    def test_maps_list(self, session):
        r = session.get(f"{API}/maps", timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_maps_palestine(self, session):
        r = session.get(f"{API}/maps/palestine", timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert d["id"] == "palestine"
        assert "locations" in d

    def test_faq(self, session):
        r = session.get(f"{API}/faq", timeout=10)
        assert r.status_code == 200

    def test_legacy_post_messages_to_self(self, session, H, auth):
        _, my_id = auth
        if not my_id:
            pytest.skip("no user_id")
        r = session.post(f"{API}/messages", headers=H,
                         json={"receiver_id": my_id, "content": "TEST_ iter40 legacy"},
                         timeout=15)
        assert r.status_code in (200, 201), r.text
        assert "message_id" in r.json()

    def test_legacy_post_messages_unknown_receiver_404(self, session, H):
        r = session.post(f"{API}/messages", headers=H,
                         json={"receiver_id": "nonexistent_xyzz", "content": "TEST_"},
                         timeout=15)
        assert r.status_code == 404
