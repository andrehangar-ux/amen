"""
Iteration 39 - Backend Refactor Validation (Fase 2 partial)
Validates:
  (a) Auth endpoints migrated to /app/backend/routes/auth.py still work
  (b) No regression in endpoints that remained in server.py
  (c) Legacy POST /api/messages (renamed function send_message_legacy) still works
  (d) Maps endpoints (used by interactive Leaflet UI)

Logout intentionally last so it doesn't invalidate the shared session token.
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "").rstrip("/")
assert BASE_URL, "EXPO_PUBLIC_BACKEND_URL not set"
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
    """Login the existing test user; register fallback if missing."""
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
    assert token, f"no session_token in response: {data}"
    return token, data.get("user", {}).get("user_id")


@pytest.fixture(scope="module")
def auth_headers(auth):
    token, _ = auth
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ============================================================
# A. AUTH ENDPOINTS (now in routes/auth.py)
# ============================================================
class TestAAuthRoutesMigration:
    """Validate all 9 auth endpoints work after migration to routes/auth.py"""

    def test_login_existing_user(self, session):
        r = session.post(f"{API}/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=20)
        assert r.status_code == 200, f"{r.status_code}: {r.text}"
        d = r.json()
        assert "session_token" in d
        assert d.get("user", {}).get("email") == EMAIL

    def test_login_wrong_password_returns_401(self, session):
        r = session.post(f"{API}/auth/login", json={"email": EMAIL, "password": "WRONG_xxx"}, timeout=20)
        assert r.status_code == 401

    def test_register_new_user(self, session):
        """Register a brand-new throwaway email and validate response shape."""
        unique = uuid.uuid4().hex[:10]
        new_email = f"TEST_iter39_{unique}@amen.com"
        payload = {
            "email": new_email,
            "password": "Test1234!",
            "name": "Iter39 Throwaway",
            "language": "it",
            "country": "IT",
            "birth_date": "1990-01-01",
        }
        r = session.post(f"{API}/auth/register", json=payload, timeout=20)
        assert r.status_code in (200, 201), f"register failed {r.status_code}: {r.text}"
        d = r.json()
        assert "session_token" in d, f"missing session_token: {d}"
        assert d.get("user", {}).get("email") == new_email
        # Stash for delete-account test
        TestAAuthRoutesMigration._throwaway_email = new_email
        TestAAuthRoutesMigration._throwaway_token = d["session_token"]

    def test_register_duplicate_email_returns_400(self, session):
        r = session.post(f"{API}/auth/register", json={
            "email": EMAIL, "password": PASSWORD, "name": "Dup",
            "language": "it", "country": "IT", "birth_date": "1990-01-01",
        }, timeout=20)
        assert r.status_code == 400, f"expected 400 dup, got {r.status_code}: {r.text}"

    def test_auth_me(self, session, auth_headers):
        r = session.get(f"{API}/auth/me", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        d = r.json()
        email = d.get("email") or d.get("user", {}).get("email")
        assert email == EMAIL

    def test_auth_me_without_token_unauthorized(self, session):
        r = session.get(f"{API}/auth/me", timeout=15)
        assert r.status_code in (401, 403)

    def test_forgot_password(self, session):
        r = session.post(f"{API}/auth/forgot-password", json={"email": EMAIL}, timeout=20)
        # Should always succeed (privacy: don't leak whether email exists)
        assert r.status_code == 200, f"{r.status_code}: {r.text}"

    def test_reset_password_invalid_token_returns_400(self, session):
        r = session.post(f"{API}/auth/reset-password", json={
            "token": "invalid-token-xyz", "new_password": "Brandnew1!"
        }, timeout=20)
        assert r.status_code in (400, 404), f"expected 400/404, got {r.status_code}: {r.text}"

    def test_google_callback_without_session_id(self, session):
        """POST /api/auth/google-callback should return 400 without session_id."""
        r = session.post(f"{API}/auth/google-callback", json={}, timeout=20)
        assert r.status_code in (400, 422), f"expected 400/422, got {r.status_code}: {r.text}"

    def test_mobile_redirect(self, session):
        """GET /api/auth/mobile-redirect should be reachable (returns HTML or redirect)."""
        r = session.get(f"{API}/auth/mobile-redirect", timeout=15, allow_redirects=False)
        # Endpoint exists - any 2xx/3xx/4xx (not 404 or 5xx) means routing works
        assert r.status_code != 404, f"endpoint not found: {r.status_code} {r.text[:200]}"
        assert r.status_code < 500, f"server error: {r.status_code} {r.text[:200]}"

    def test_delete_account_throwaway_user(self, session):
        """Delete the throwaway user created in test_register_new_user."""
        token = getattr(TestAAuthRoutesMigration, "_throwaway_token", None)
        if not token:
            pytest.skip("throwaway user not created")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        r = session.delete(f"{API}/auth/delete-account", headers=headers, timeout=20)
        assert r.status_code in (200, 204), f"{r.status_code}: {r.text}"

        # Verify user actually deleted: login should now fail
        login_after = session.post(f"{API}/auth/login", json={
            "email": getattr(TestAAuthRoutesMigration, "_throwaway_email"),
            "password": "Test1234!",
        }, timeout=15)
        assert login_after.status_code == 401, \
            f"deleted user can still login: {login_after.status_code}"


# ============================================================
# B. REGRESSION - public/non-auth endpoints still in server.py
# ============================================================
class TestBRegressionPublic:
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

    def test_bible_daily_verse_it(self, session):
        r = session.get(f"{API}/bible/daily-verse?lang=it", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "reference" in d and "text" in d

    def test_forum_categories(self, session):
        r = session.get(f"{API}/forum/categories", timeout=10)
        assert r.status_code == 200

    def test_dictionary_it(self, session):
        r = session.get(f"{API}/dictionary?lang=it", timeout=15)
        assert r.status_code == 200

    def test_quiz_topics(self, session):
        r = session.get(f"{API}/quiz/topics", timeout=10)
        assert r.status_code == 200


# ============================================================
# C. REGRESSION - authenticated endpoints
# ============================================================
class TestCRegressionAuthenticated:
    def test_community_messages_post_with_message_type(self, session, auth_headers):
        payload = {"content": "TEST_ iter39 community", "language": "it", "message_type": "text"}
        r = session.post(f"{API}/community/messages", headers=auth_headers, json=payload, timeout=20)
        assert r.status_code == 200, f"{r.status_code}: {r.text}"
        d = r.json()
        assert d.get("message_type") == "text"
        assert "message_id" in d

    def test_private_messages_conversations(self, session, auth_headers):
        r = session.get(f"{API}/private-messages/conversations", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_parental_can_use_social(self, session, auth_headers):
        r = session.get(f"{API}/parental-controls/can-use-social", headers=auth_headers, timeout=15)
        assert r.status_code == 200


# ============================================================
# D. LEGACY POST /api/messages (renamed function send_message_legacy)
# ============================================================
class TestDLegacyMessagesEndpoint:
    """The old POST /api/messages was a duplicate of /api/private-messages.
    Function was renamed to send_message_legacy; route must still respond."""

    def test_legacy_messages_requires_auth(self, session):
        r = session.post(f"{API}/messages", json={"receiver_id": "x", "content": "y"}, timeout=15)
        assert r.status_code in (401, 403), f"expected auth-required, got {r.status_code}: {r.text}"

    def test_legacy_messages_unknown_receiver_returns_404(self, session, auth_headers, auth):
        _, my_user_id = auth
        # Use clearly invalid receiver_id
        payload = {"receiver_id": "nonexistent_user_xxxx", "content": "TEST_ legacy ping"}
        r = session.post(f"{API}/messages", headers=auth_headers, json=payload, timeout=15)
        assert r.status_code == 404, \
            f"expected 404 unknown receiver, got {r.status_code}: {r.text}"

    def test_legacy_messages_send_to_self_succeeds(self, session, auth_headers, auth):
        """Send to ourselves to verify happy path with valid receiver_id."""
        _, my_user_id = auth
        if not my_user_id:
            pytest.skip("no user_id available")
        payload = {"receiver_id": my_user_id, "content": "TEST_ iter39 legacy self"}
        r = session.post(f"{API}/messages", headers=auth_headers, json=payload, timeout=15)
        assert r.status_code in (200, 201), f"{r.status_code}: {r.text}"
        d = r.json()
        assert "message_id" in d


# ============================================================
# E. MAPS ENDPOINTS (used by Leaflet UI)
# ============================================================
class TestEMaps:
    def test_maps_list_returns_4(self, session):
        r = session.get(f"{API}/maps", timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d, list)
        assert len(d) == 4, f"expected 4 maps, got {len(d)}: {[m.get('id') for m in d]}"
        ids = {m["id"] for m in d}
        assert {"palestine", "exodus", "paul_journeys"}.issubset(ids), f"missing core maps in {ids}"

    def test_maps_palestine_has_8_locations_and_center(self, session):
        r = session.get(f"{API}/maps/palestine", timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert d["id"] == "palestine"
        assert d["name"] == "Terra Santa"
        assert "center" in d and "lat" in d["center"] and "lng" in d["center"]
        assert isinstance(d["center"]["lat"], (int, float))
        assert isinstance(d["center"]["lng"], (int, float))
        assert isinstance(d["locations"], list)
        assert len(d["locations"]) == 8, f"expected 8 locations, got {len(d['locations'])}"
        # Each location must have required keys for Leaflet markers
        for loc in d["locations"]:
            assert "name" in loc and "lat" in loc and "lng" in loc and "type" in loc

    def test_maps_nonexistent_returns_404(self, session):
        r = session.get(f"{API}/maps/does_not_exist_xyz", timeout=10)
        assert r.status_code == 404


# ============================================================
# Z. LOGOUT (must run last)
# ============================================================
class TestZLogout:
    def test_logout(self, session, auth_headers):
        r = session.post(f"{API}/auth/logout", headers=auth_headers, timeout=15)
        assert r.status_code == 200
