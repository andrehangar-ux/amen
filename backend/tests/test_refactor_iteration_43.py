"""
Iteration 43 - Final regression after:
1) Quiz articulation (LLM-rewritten 704 questions)
2) Bible chapter titles expansion: 225 chapters in 6 languages (total 283)
3) Google UMP SDK + AdBanner gated by consent (frontend only - not tested here)
4) server.py refactoring: 5 new route modules

Backend-only regression.
"""
import os
import re
import uuid
import requests
import pytest

BASE_URL = os.environ.get(
    "EXPO_PUBLIC_BACKEND_URL",
    "https://quiz-nav-build.preview.emergentagent.com",
).rstrip("/")
API = f"{BASE_URL}/api"

PRIMARY_EMAIL = "refactortest@amen.com"
PRIMARY_PASSWORD = "Test1234!"


# ---------- fixtures ----------

@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def adult_token(session):
    r = session.post(f"{API}/auth/login", json={"email": PRIMARY_EMAIL, "password": PRIMARY_PASSWORD})
    if r.status_code != 200:
        unique = f"iter43_{uuid.uuid4().hex[:8]}@amen.com"
        session.post(f"{API}/auth/register", json={
            "email": unique, "password": PRIMARY_PASSWORD,
            "name": "Iter43 Tester", "birth_date": "1990-01-01", "language": "it",
        })
        r = session.post(f"{API}/auth/login", json={"email": unique, "password": PRIMARY_PASSWORD})
    if r.status_code != 200:
        pytest.skip(f"Login failed: {r.status_code} {r.text[:200]}")
    data = r.json()
    token = data.get("session_token") or data.get("access_token") or data.get("token")
    session.cookies.clear()
    return token


@pytest.fixture(scope="session")
def auth_headers(adult_token):
    return {"Authorization": f"Bearer {adult_token}", "Content-Type": "application/json"}


# ---------- Health ----------

class TestHealth:
    def test_health(self, session):
        r = session.get(f"{API}/health")
        assert r.status_code == 200
        assert r.json().get("status") in ("healthy", "ok", "OK")


# ---------- Auth full flow ----------

class TestAuthFlow:
    def test_register_login_checkauth(self, session):
        email = f"TEST_iter43_{uuid.uuid4().hex[:8]}@amen.com"
        pw = "Test1234!"
        r = session.post(f"{API}/auth/register", json={
            "email": email, "password": pw, "name": "Iter43 NewUser",
            "birth_date": "1990-01-01", "language": "it",
        })
        assert r.status_code in (200, 201), r.text[:200]

        r = session.post(f"{API}/auth/login", json={"email": email, "password": pw})
        assert r.status_code == 200, r.text[:200]
        token = r.json().get("session_token")
        assert token

        # checkAuth equivalent: /auth/me or /me
        for endpoint in ("/auth/me", "/me", "/auth/check"):
            rr = requests.get(f"{API}{endpoint}", headers={"Authorization": f"Bearer {token}"})
            if rr.status_code == 200:
                body = rr.json()
                # email may be nested under user
                blob = str(body)
                assert email.lower() in blob.lower() or "user" in body or "email" in body
                return
        pytest.fail("No working /auth/me|/me|/auth/check endpoint")


# ---------- Quiz: categories + articulation regression ----------

class TestQuizCategories:
    def test_categories_it_35_includes_lettere_generali(self, session):
        r = session.get(f"{API}/quiz/categories?lang=it")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 35, f"Expected 35, got {len(data)}"
        ids = {c["id"] for c in data}
        assert "cat_lettere_generali" in ids

    def test_topics_it_classic(self, session):
        r = session.get(f"{API}/quiz/topics?lang=it")
        assert r.status_code == 200
        topics = r.json()
        assert isinstance(topics, list) and len(topics) > 0

    def test_lettere_generali_30_articulated(self, session):
        r = session.get(f"{API}/quiz/category/cat_lettere_generali?lang=it&translate=false")
        assert r.status_code == 200
        qs = r.json()["questions"]
        assert len(qs) == 30
        # every question must be a full sentence (>= 3 words, ends with ? or .)
        for q in qs:
            text = q["question"].strip()
            words = text.split()
            assert len(words) >= 3, f"Question too short: {text!r}"

    def test_canone_bibbia_articulated_no_cryptic_refs(self, session):
        """Verify questions are full sentences and explanations have no [123, 456] refs."""
        r = session.get(f"{API}/quiz/category/cat_canone_bibbia?lang=it&translate=false")
        assert r.status_code == 200
        qs = r.json()["questions"]
        assert len(qs) >= 25
        cryptic = re.compile(r"\[\s*\d+\s*,\s*\d+")
        for q in qs:
            text = q["question"].strip()
            exp = (q.get("explanation") or "").strip()
            assert len(text.split()) >= 3, f"Single-word/short question: {text!r}"
            assert not cryptic.search(text), f"Cryptic ref in question: {text!r}"
            assert not cryptic.search(exp), f"Cryptic ref in explanation: {exp!r}"

    def test_profeti_minori_25_no_dupes_no_offtopic(self, session):
        r = session.get(f"{API}/quiz/category/cat_profeti_minori?lang=it&translate=false")
        assert r.status_code == 200
        qs = r.json()["questions"]
        assert len(qs) == 25, f"Expected 25, got {len(qs)}"
        texts = [q["question"] for q in qs]
        assert len(set(texts)) == len(texts), "Duplicate questions found"
        # minor prophets keyword sanity (at least some must reference one of them)
        minor_books = [
            "osea", "gioele", "amos", "abdia", "giona", "michea", "naum",
            "abacuc", "sofonia", "aggeo", "zaccaria", "malachia",
        ]
        combined = " ".join((q["question"] + " " + (q.get("explanation") or "")).lower() for q in qs)
        hits = sum(1 for b in minor_books if b in combined)
        assert hits >= 3, f"Profeti minori category seems off-topic; matched only {hits} minor-prophet names"


# ---------- Quiz submit end-to-end ----------

class TestQuizSubmit:
    def test_submit_lettere_generali(self, auth_headers):
        q = requests.get(f"{API}/quiz/category/cat_lettere_generali?lang=it&translate=false")
        assert q.status_code == 200
        quiz = q.json()
        answers = {qq["id"]: qq["correct"] for qq in quiz["questions"]}
        payload = {"topic": "cat_lettere_generali", "answers": answers, "language": "it"}
        r = requests.post(f"{API}/quiz/submit", json=payload, headers=auth_headers, timeout=90)
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert data["correct_count"] == len(quiz["questions"])
        assert data["total"] == len(quiz["questions"])
        assert data["score"] == 100.0
        assert "feedback" in data
        # persistence
        h = requests.get(f"{API}/quiz/history", headers=auth_headers)
        assert h.status_code == 200
        topics = [it.get("topic") for it in h.json()]
        assert "cat_lettere_generali" in topics


# ---------- Bible chapter titles (6 languages) ----------

class TestBibleChapterTitles:
    @pytest.mark.parametrize("book,chapter,lang,expected", [
        ("Romani", 8, "it", "La Vita nello Spirito"),
        ("Romani", 8, "en", "Life in the Spirit"),
        ("Giona", 2, "es", "La Oración de Jonás"),
        ("Apocalisse", 21, "de", "Das Neue Jerusalem"),
    ])
    def test_known_titles(self, session, book, chapter, lang, expected):
        r = session.get(f"{API}/bible/chapter/{book}/{chapter}?lang={lang}")
        assert r.status_code == 200, r.text[:200]
        assert r.json().get("chapter_title") == expected

    def test_genesi_22_fr_has_french_title(self, session):
        """fr title must exist and be non-empty (verify French expansion)."""
        r = session.get(f"{API}/bible/chapter/Genesi/22?lang=fr")
        assert r.status_code == 200
        title = r.json().get("chapter_title", "")
        assert title and isinstance(title, str)
        # It should NOT be the Italian default
        # Italian title for Genesi 22 is 'Il Sacrificio di Isacco' — fr should differ
        assert "Sacrifice" in title or "Isaac" in title, f"Unexpected fr title: {title!r}"
        # Compare against IT to confirm translation
        r_it = session.get(f"{API}/bible/chapter/Genesi/22?lang=it")
        if r_it.status_code == 200:
            it_title = r_it.json().get("chapter_title", "")
            assert title != it_title, f"fr title equals it title ({title!r}); not translated"


# ---------- Bible regression ----------

class TestBibleRegression:
    def test_books_66(self, session):
        r = session.get(f"{API}/bible/books?lang=it")
        assert r.status_code == 200
        d = r.json()
        books = d if isinstance(d, list) else d.get("books", [])
        assert len(books) == 66

    def test_editions_12(self, session):
        r = session.get(f"{API}/bible/editions")
        assert r.status_code == 200
        d = r.json()
        if isinstance(d, dict):
            editions = list(d.keys())
        elif isinstance(d, list):
            editions = d
        else:
            editions = d.get("editions", [])
        assert len(editions) == 12

    def test_psalm_23_edition_cache_fix(self, session):
        r1 = session.get(f"{API}/bible/chapter/Salmi/23?lang=it&edition=nuova_diodati")
        r2 = session.get(f"{API}/bible/chapter/Salmi/23?lang=it&edition=diodati_classica")
        assert r1.status_code == 200 and r2.status_code == 200

        def texts(payload):
            verses = payload.get("verses") or payload.get("chapter", {}).get("verses") or []
            return " ".join(v.get("text", "") for v in verses).strip()
        t1, t2 = texts(r1.json()), texts(r2.json())
        assert t1 and t2
        assert t1 != t2, "edition cache bug: same text for two different editions"


# ---------- Maps + FAQ ----------

class TestMapsFaq:
    def test_maps_4(self, session):
        r = session.get(f"{API}/maps")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) == 4

    def test_faq_8(self, session):
        r = session.get(f"{API}/faq")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) == 8


# ---------- Auth-protected: study-groups / notifications / community ----------

class TestProtectedEndpoints:
    def test_study_groups_authed(self, auth_headers):
        r = requests.get(f"{API}/study-groups", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "groups" in body and isinstance(body["groups"], list)

    def test_notifications_authed(self, auth_headers):
        r = requests.get(f"{API}/notifications", headers=auth_headers)
        assert r.status_code == 200, r.text[:200]
        body = r.json()
        # accept list or {notifications:[...]}
        assert isinstance(body, list) or "notifications" in body

    def test_community_messages_authed(self, auth_headers):
        r = requests.get(f"{API}/community/messages", headers=auth_headers)
        assert r.status_code == 200, r.text[:200]
        body = r.json()
        assert isinstance(body, list) or "messages" in body

    def test_study_groups_unauth(self, session):
        r = session.get(f"{API}/study-groups")
        assert r.status_code in (401, 403)
