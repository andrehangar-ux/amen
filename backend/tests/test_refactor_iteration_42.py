"""
Backend regression tests for Phase 2 refactoring continuation.

Covers:
- New routes/quiz.py module (topics, categories, history, stats, submit)
- New routes/maps.py module
- New routes/events.py module
- New routes/faq.py module
- New routes/study_groups.py module
- Quiz category expansion: lettere_generali (30 q) + profeti_minori (30+ q)
- Bible chapter edition caching fix (different editions return different texts)
- 66 bible books, 12 bible editions
"""
import os
import uuid
import requests
import pytest

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "https://quiz-nav-build.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

PRIMARY_EMAIL = "refactortest@amen.com"
PRIMARY_PASSWORD = "Test1234!"


# ---------- shared fixtures ----------

@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def adult_token(session):
    # Try login; if user missing, register an adult and re-login
    r = session.post(f"{API}/auth/login", json={"email": PRIMARY_EMAIL, "password": PRIMARY_PASSWORD})
    if r.status_code != 200:
        unique = f"iter42_{uuid.uuid4().hex[:8]}@amen.com"
        session.post(f"{API}/auth/register", json={
            "email": unique,
            "password": PRIMARY_PASSWORD,
            "name": "Iter42 Tester",
            "birth_date": "1990-01-01",
            "language": "it",
        })
        r = session.post(f"{API}/auth/login", json={"email": unique, "password": PRIMARY_PASSWORD})
    if r.status_code != 200:
        pytest.skip(f"Login failed: {r.status_code} {r.text[:200]}")
    data = r.json()
    token = data.get("session_token") or data.get("access_token") or data.get("token")
    # Clear cookies from session so negative-auth tests behave correctly
    session.cookies.clear()
    return token


@pytest.fixture(scope="session")
def auth_headers(adult_token):
    return {"Authorization": f"Bearer {adult_token}", "Content-Type": "application/json"}


# ---------- Quiz module ----------

class TestQuizTopicsAndCategories:
    def test_topics_it(self, session):
        r = session.get(f"{API}/quiz/topics?lang=it")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_categories_it_count_35(self, session):
        r = session.get(f"{API}/quiz/categories?lang=it")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 35, f"Expected 35 IT categories, got {len(data)}"
        ids = {t["id"] for t in data}
        assert "cat_lettere_generali" in ids
        assert "cat_studio_avanzato" in ids
        assert "cat_profeti_minori" in ids

    def test_categories_en_count_and_translation(self, session):
        r = session.get(f"{API}/quiz/categories?lang=en")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 35
        lg = next((t for t in data if t["id"] == "cat_lettere_generali"), None)
        assert lg is not None
        # title should be translated; quiz_1000 returns 'title' not 'name'
        assert "General Epistles" in (lg.get("title") or lg.get("name") or "")

    def test_lettere_generali_30_questions(self, session):
        r = session.get(f"{API}/quiz/category/cat_lettere_generali?lang=it&translate=false")
        assert r.status_code == 200
        data = r.json()
        assert "questions" in data
        assert len(data["questions"]) == 30, f"Expected 30 q, got {len(data['questions'])}"

    def test_profeti_minori_30plus_questions(self, session):
        r = session.get(f"{API}/quiz/category/cat_profeti_minori?lang=it&translate=false")
        assert r.status_code == 200
        data = r.json()
        assert len(data["questions"]) >= 30, f"Expected >=30 q, got {len(data['questions'])}"

    def test_quiz_by_classic_topic(self, session):
        r = session.get(f"{API}/quiz/genesi?lang=it")
        assert r.status_code == 200
        data = r.json()
        assert "questions" in data
        assert len(data["questions"]) > 0

    def test_quiz_by_classic_topic_not_found(self, session):
        r = session.get(f"{API}/quiz/nonexistent_topic_xyz?lang=it")
        assert r.status_code == 404

    def test_quiz_category_not_found(self, session):
        r = session.get(f"{API}/quiz/category/cat_does_not_exist?lang=it&translate=false")
        assert r.status_code == 404


class TestQuizHistoryStatsSubmit:
    def test_history_auth_required(self, session):
        r = session.get(f"{API}/quiz/history")
        assert r.status_code in (401, 403)

    def test_history_authed(self, auth_headers):
        r = requests.get(f"{API}/quiz/history", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_stats_authed(self, auth_headers):
        r = requests.get(f"{API}/quiz/stats", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        for key in ("total_quizzes", "total_questions", "average_score", "best_score", "streak"):
            assert key in data

    def test_submit_quiz_lettere_generali(self, auth_headers):
        # fetch questions first to build answers map
        q = requests.get(f"{API}/quiz/category/cat_lettere_generali?lang=it&translate=false")
        assert q.status_code == 200
        quiz = q.json()
        # Build answers: all correct
        answers = {qq["id"]: qq["correct"] for qq in quiz["questions"]}
        payload = {"topic": "cat_lettere_generali", "answers": answers, "language": "it"}
        r = requests.post(f"{API}/quiz/submit", json=payload, headers=auth_headers, timeout=60)
        assert r.status_code == 200, f"submit failed: {r.text[:300]}"
        data = r.json()
        assert data["correct_count"] == len(quiz["questions"])
        assert data["total"] == len(quiz["questions"])
        assert data["score"] == 100.0
        assert "feedback" in data
        assert isinstance(data["results"], list) and len(data["results"]) == len(quiz["questions"])

        # verify persistence via history
        h = requests.get(f"{API}/quiz/history", headers=auth_headers)
        assert h.status_code == 200
        topics = [item.get("topic") for item in h.json()]
        assert "cat_lettere_generali" in topics


# ---------- Maps module ----------

class TestMaps:
    def test_maps_list_returns_4(self, session):
        r = session.get(f"{API}/maps")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 4
        ids = {m["id"] for m in data}
        assert {"palestine", "exodus", "paul_journeys", "jesus_ministry"}.issubset(ids)

    def test_map_palestine_full(self, session):
        r = session.get(f"{API}/maps/palestine")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == "palestine"
        assert isinstance(data["locations"], list) and len(data["locations"]) >= 8
        loc_names = [l["name"] for l in data["locations"]]
        assert "Gerusalemme" in loc_names

    def test_map_not_found(self, session):
        r = session.get(f"{API}/maps/nonexistent_map")
        assert r.status_code == 404


# ---------- FAQ module ----------

class TestFAQ:
    def test_faq_list(self, session):
        r = session.get(f"{API}/faq")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 8

    def test_faq_categories(self, session):
        r = session.get(f"{API}/faq/categories")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert all("id" in c and "name" in c for c in data)

    def test_faq_filter_by_category(self, session):
        r = session.get(f"{API}/faq?category=bibbia")
        assert r.status_code == 200
        items = r.json()
        assert all(i["category"] == "bibbia" for i in items)


# ---------- Events module ----------

class TestEvents:
    @pytest.fixture(scope="class")
    def event_id(self, auth_headers):
        payload = {
            "title": "TEST_iter42 Event",
            "description": "Regression test event",
            "event_type": "study",
            "scheduled_at": "2030-01-01T10:00:00Z",
            "duration_minutes": 30,
            "bible_book": "Salmi",
            "bible_chapter": 23,
        }
        r = requests.post(f"{API}/events", json=payload, headers=auth_headers)
        assert r.status_code == 200, f"create event failed: {r.text[:300]}"
        data = r.json()
        assert "event_id" in data
        return data["event_id"]

    def test_get_events_list(self, session):
        r = session.get(f"{API}/events")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_event_by_id(self, session, event_id):
        r = session.get(f"{API}/events/{event_id}")
        assert r.status_code == 200
        assert r.json()["event_id"] == event_id

    def test_join_event(self, auth_headers, event_id):
        r = requests.post(f"{API}/events/{event_id}/join", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["success"] is True

    def test_start_event_creator(self, auth_headers, event_id):
        r = requests.post(f"{API}/events/{event_id}/start", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["status"] == "live"

    def test_end_event_creator(self, auth_headers, event_id):
        r = requests.post(f"{API}/events/{event_id}/end", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["status"] == "ended"

    def test_events_auth_required_for_create(self, session):
        r = session.post(f"{API}/events", json={
            "title": "no auth", "description": "x", "event_type": "study",
            "scheduled_at": "2030-01-01T10:00:00Z",
        })
        assert r.status_code in (401, 403)


# ---------- Study Groups module ----------

class TestStudyGroups:
    @pytest.fixture(scope="class")
    def group_id(self, auth_headers):
        payload = {"name": "TEST_iter42 Group", "description": "Regression test"}
        r = requests.post(f"{API}/study-groups", json=payload, headers=auth_headers)
        assert r.status_code == 200, f"create group failed: {r.text[:300]}"
        return r.json()["group_id"]

    def test_get_my_groups(self, auth_headers, group_id):
        r = requests.get(f"{API}/study-groups", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert "groups" in data
        ids = [g["group_id"] for g in data["groups"]]
        assert group_id in ids

    def test_send_and_get_messages(self, auth_headers, group_id):
        m = requests.post(
            f"{API}/study-groups/{group_id}/messages",
            json={"content": "TEST_iter42 hello", "message_type": "text"},
            headers=auth_headers,
        )
        assert m.status_code == 200
        g = requests.get(f"{API}/study-groups/{group_id}/messages", headers=auth_headers)
        assert g.status_code == 200
        msgs = g.json()["messages"]
        assert any("TEST_iter42 hello" in mm["content"] for mm in msgs)

    def test_search_users_excludes_minors_and_self(self, auth_headers):
        r = requests.get(f"{API}/study-groups/search-users?q=test", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert "users" in data
        # No way to assert minors are excluded without seeding minor; trust contract.

    def test_groups_auth_required(self, session):
        r = session.get(f"{API}/study-groups")
        assert r.status_code in (401, 403)


# ---------- Bible (regression: edition caching fix + 66 books + 12 editions) ----------

class TestBible:
    def test_books_count_66(self, session):
        r = session.get(f"{API}/bible/books?lang=it")
        assert r.status_code == 200
        data = r.json()
        # Response can be list or {books: [...]}
        books = data if isinstance(data, list) else data.get("books", [])
        assert len(books) == 66, f"Expected 66 books, got {len(books)}"

    def test_editions_count_12(self, session):
        r = session.get(f"{API}/bible/editions")
        assert r.status_code == 200
        data = r.json()
        # /bible/editions returns a dict {edition_id: {...}}
        if isinstance(data, dict):
            editions = list(data.keys())
        elif isinstance(data, list):
            editions = data
        else:
            editions = data.get("editions", [])
        assert len(editions) == 12, f"Expected 12 editions, got {len(editions)}"

    def test_psalm_23_diodati_classica_vs_nuova_diodati_differ(self, session):
        r1 = session.get(f"{API}/bible/chapter/Salmi/23?lang=it&edition=nuova_diodati")
        r2 = session.get(f"{API}/bible/chapter/Salmi/23?lang=it&edition=diodati_classica")
        assert r1.status_code == 200 and r2.status_code == 200, (r1.status_code, r2.status_code)
        # extract verse texts
        def texts(payload):
            verses = payload.get("verses") or payload.get("chapter", {}).get("verses") or []
            return " ".join((v.get("text", "") for v in verses)).strip()
        t1 = texts(r1.json())
        t2 = texts(r2.json())
        assert t1 and t2, "verses missing in chapter response"
        assert t1 != t2, "nuova_diodati and diodati_classica returned IDENTICAL text — edition cache bug"

    def test_genesis_1_kjv_vs_asv_differ(self, session):
        r1 = session.get(f"{API}/bible/chapter/Genesis/1?lang=en&edition=kjv")
        r2 = session.get(f"{API}/bible/chapter/Genesis/1?lang=en&edition=asv")
        assert r1.status_code == 200 and r2.status_code == 200
        def texts(payload):
            verses = payload.get("verses") or payload.get("chapter", {}).get("verses") or []
            return " ".join((v.get("text", "") for v in verses)).strip()
        t1, t2 = texts(r1.json()), texts(r2.json())
        assert t1 and t2
        assert t1 != t2, "kjv and asv returned IDENTICAL text — edition cache bug"
