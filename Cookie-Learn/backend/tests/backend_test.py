
import io
import os
import time
import uuid

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8000").rstrip("/")
API = f"{BASE_URL}/api"

DEMO = {"email": "demo@cookielearn.app", "password": "demo123"}
ADMIN = {"email": "admin@cookielearn.app", "password": "admin123"}

AI_TIMEOUT = 60



@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def demo_token(session):
    r = session.post(f"{API}/auth/login", json=DEMO, timeout=15)
    assert r.status_code == 200, f"demo login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def admin_token(session):
    r = session.post(f"{API}/auth/login", json=ADMIN, timeout=15)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def new_user(session):

    suffix = uuid.uuid4().hex[:8]
    body = {
        "email": f"test_{suffix}@example.com",
        "username": f"test_{suffix}",
        "password": "testpass123",
        "full_name": "Test User",
        "native_language_code": "en",
    }
    r = session.post(f"{API}/auth/register", json=body, timeout=15)
    assert r.status_code == 200, f"register failed: {r.status_code} {r.text}"
    d = r.json()
    return {"token": d["access_token"], "user": d["user"], "password": body["password"], "email": body["email"]}


def auth_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}



class TestAuth:
    def test_register_returns_jwt_and_user(self, new_user):
        assert isinstance(new_user["token"], str) and len(new_user["token"]) > 20
        assert new_user["user"]["email"] == new_user["email"]
        assert new_user["user"]["hearts"] >= 0

    def test_login_demo(self, session):
        r = session.post(f"{API}/auth/login", json=DEMO, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["user"]["email"] == DEMO["email"]
        assert "access_token" in d

    def test_login_bad_password(self, session):
        r = session.post(f"{API}/auth/login", json={"email": DEMO["email"], "password": "wrong"}, timeout=15)
        assert r.status_code == 401

    def test_me_returns_user(self, session, demo_token):
        r = session.get(f"{API}/auth/me", headers=auth_headers(demo_token), timeout=15)
        assert r.status_code == 200
        assert r.json()["email"] == DEMO["email"]

    def test_me_unauth(self, session):
        r = session.get(f"{API}/auth/me", timeout=15)
        assert r.status_code in (401, 403)

    def test_change_password(self, session, new_user):

        r = session.post(
            f"{API}/auth/change-password",
            json={"current_password": new_user["password"], "new_password": "newpass456"},
            headers=auth_headers(new_user["token"]),
            timeout=15,
        )
        assert r.status_code == 200, r.text

        r2 = session.post(f"{API}/auth/login", json={"email": new_user["email"], "password": "newpass456"}, timeout=15)
        assert r2.status_code == 200

        r3 = session.post(
            f"{API}/auth/change-password",
            json={"current_password": "newpass456", "new_password": new_user["password"]},
            headers=auth_headers(new_user["token"]),
            timeout=15,
        )
        assert r3.status_code == 200



class TestLanguages:
    def test_list_languages(self, session):
        r = session.get(f"{API}/languages", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 10, f"Expected 10 languages, got {len(data)}"
        codes = {l["code"] for l in data}
        expected = {"en", "tr", "az", "de", "fr", "es", "it", "ja", "ko", "ru"}
        assert expected.issubset(codes), f"Missing: {expected - codes}"

    def test_curriculum_requires_auth(self, session):
        r = session.get(f"{API}/languages/en/curriculum", timeout=15)
        assert r.status_code in (401, 403)

    def test_curriculum_en(self, session, demo_token):
        r = session.get(f"{API}/languages/en/curriculum", headers=auth_headers(demo_token), timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) > 0
        u0 = data[0]
        assert "sections" in u0 and len(u0["sections"]) > 0
        assert "lessons" in u0["sections"][0]

    def test_lesson_questions_no_correct_answer_exposed(self, session, demo_token):
        r = session.get(f"{API}/languages/en/curriculum", headers=auth_headers(demo_token), timeout=20)
        lessons = []
        for u in r.json():
            for s in u["sections"]:
                lessons.extend(s["lessons"])

        lesson = next((l for l in lessons if not l.get("is_ai_dynamic")), lessons[0])
        rid = lesson["id"]
        r2 = session.get(f"{API}/languages/lessons/{rid}/questions", headers=auth_headers(demo_token), timeout=20)
        assert r2.status_code == 200, r2.text
        qs = r2.json()
        assert isinstance(qs, list)
        if qs:
            for q in qs:
                assert "correct_answer" not in q, "correct_answer should not be exposed in public endpoint"
            pytest.lesson_with_qs = rid
            pytest.first_q = qs[0]

    def test_check_answer(self, session, demo_token):

        r = session.get(f"{API}/languages/en/curriculum", headers=auth_headers(demo_token), timeout=20)
        found = None
        for u in r.json():
            for s in u["sections"]:
                for l in s["lessons"]:
                    if not l.get("is_ai_dynamic"):
                        qr = session.get(f"{API}/languages/lessons/{l['id']}/questions", headers=auth_headers(demo_token), timeout=15)
                        if qr.status_code == 200 and qr.json():
                            found = (l["id"], qr.json()[0])
                            break
                if found:
                    break
            if found:
                break
        if not found:
            pytest.skip("No real (non-AI) lessons with questions")
        lid, q = found
        r2 = session.post(
            f"{API}/languages/lessons/{lid}/check-answer",
            json={"question_id": q["id"], "user_answer": "definitely_wrong_xyz"},
            headers=auth_headers(demo_token),
            timeout=15,
        )
        assert r2.status_code == 200
        assert r2.json()["is_correct"] is False
        correct = r2.json()["correct_answer"]

        r3 = session.post(
            f"{API}/languages/lessons/{lid}/check-answer",
            json={"question_id": q["id"], "user_answer": correct},
            headers=auth_headers(demo_token),
            timeout=15,
        )
        assert r3.json()["is_correct"] is True



class TestProgress:
    def _find_lesson_and_question(self, session, token):
        r = session.get(f"{API}/languages/en/curriculum", headers=auth_headers(token), timeout=20)
        for u in r.json():
            for s in u["sections"]:
                for l in s["lessons"]:
                    if not l.get("is_ai_dynamic"):
                        qr = session.get(f"{API}/languages/lessons/{l['id']}/questions", headers=auth_headers(token), timeout=15)
                        if qr.status_code == 200 and qr.json():
                            return l["id"], qr.json()[0]
        return None, None

    def test_submit_answer_wrong_decrements_hearts(self, session, new_user):
        token = new_user["token"]
        lid, q = self._find_lesson_and_question(session, token)
        if not lid:
            pytest.skip("No lesson found")

        me = session.get(f"{API}/auth/me", headers=auth_headers(token), timeout=15).json()
        h0 = me["hearts"]
        body = {
            "question_id": q["id"],
            "lesson_id": lid,
            "question_type": q["type"],
            "prompt": q["prompt"],
            "user_answer": "definitely_wrong",
            "correct_answer": "something_else",
            "is_correct": False,
            "language_code": "en",
        }
        r = session.post(f"{API}/progress/answer", json=body, headers=auth_headers(token), timeout=15)
        assert r.status_code == 200
        h1 = r.json()["hearts"]
        assert h1 == max(0, h0 - 1), f"Expected {h0-1}, got {h1}"

    def test_complete_lesson_awards_xp_and_updates_streak(self, session, new_user):
        token = new_user["token"]
        lid, _ = self._find_lesson_and_question(session, token)
        if not lid:
            pytest.skip("No lesson found")
        me_before = session.get(f"{API}/auth/me", headers=auth_headers(token), timeout=15).json()
        r = session.post(
            f"{API}/progress/complete-lesson",
            json={"lesson_id": lid, "correct_count": 5, "total_count": 5, "duration_seconds": 60},
            headers=auth_headers(token),
            timeout=20,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["xp_earned"] > 0
        assert d["streak_days"] >= 1
        assert d["daily_xp_earned"] >= d["xp_earned"] or d["daily_xp_earned"] >= me_before["daily_xp_earned"]
        assert "new_achievements" in d

    def test_daily_quests(self, session, demo_token):
        r = session.get(f"{API}/progress/daily-quests", headers=auth_headers(demo_token), timeout=15)
        assert r.status_code == 200
        quests = r.json()
        assert isinstance(quests, list) and len(quests) == 3
        types = {q["quest_type"] for q in quests}
        assert {"earn_xp", "complete_lessons", "perfect_lesson"}.issubset(types)



class TestStats:
    def test_stats_me(self, session, demo_token):
        r = session.get(f"{API}/stats/me", headers=auth_headers(demo_token), timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "daily_xp" in d
        assert len(d["daily_xp"]) == 14, f"Expected 14 daily_xp points, got {len(d['daily_xp'])}"
        assert "accuracy" in d and 0.0 <= d["accuracy"] <= 1.0
        assert d["xp_total"] >= 0

    def test_achievements(self, session, demo_token):
        r = session.get(f"{API}/stats/achievements", headers=auth_headers(demo_token), timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 12, f"Expected 12 achievements, got {len(data)}"
        for a in data:
            assert "unlocked" in a

    def test_leaderboard(self, session, demo_token):
        r = session.get(f"{API}/leaderboard", headers=auth_headers(demo_token), timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "tier" in d and "entries" in d



class TestUsers:
    def test_update_profile(self, session, new_user):
        payload = {
            "full_name": "Updated Name",
            "bio": "hello",
            "native_language_code": "en",
            "level_code": "A2",
            "daily_goal_xp": 30,
        }
        r = session.patch(f"{API}/users/me", json=payload, headers=auth_headers(new_user["token"]), timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["full_name"] == "Updated Name"
        assert d["bio"] == "hello"
        assert d["native_language_code"] == "en"
        assert d["level_code"] == "A2"
        assert d["daily_goal_xp"] == 30

    def test_avatar_upload(self, session, new_user):

        png = bytes.fromhex(
            "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C4890000000D49444154789C63F8CFC0000000030001"
            "5C0DE0B90000000049454E44AE426082"
        )
        files = {"file": ("a.png", io.BytesIO(png), "image/png")}
        headers = {"Authorization": f"Bearer {new_user['token']}"}
        r = requests.post(f"{API}/users/me/avatar", files=files, headers=headers, timeout=20)
        assert r.status_code == 200, r.text
        assert r.json()["avatar_url"], "avatar_url missing"

    def test_active_language(self, session, new_user):
        r = session.post(
            f"{API}/users/me/active-language?code=en",
            headers=auth_headers(new_user["token"]),
            timeout=15,
        )
        assert r.status_code == 200
        assert r.json()["active_language_code"] == "en"

    def test_refill_hearts(self, session, new_user):
        token = new_user["token"]

        me = session.get(f"{API}/auth/me", headers=auth_headers(token), timeout=15).json()
        if me["hearts"] == me["max_hearts"]:

            r = session.post(f"{API}/users/me/refill-hearts", headers=auth_headers(token), timeout=15)
            assert r.status_code == 200
            return
        gems_before = me["gems"]
        r = session.post(f"{API}/users/me/refill-hearts", headers=auth_headers(token), timeout=15)
        if r.status_code == 400:

            assert "gem" in r.text.lower() or "insufficient" in r.text.lower()
            return
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["hearts"] == d["max_hearts"]
        assert d["gems"] <= gems_before



class TestAI:
    def test_ai_chat_teacher(self, session, demo_token):
        r = session.post(
            f"{API}/ai/chat",
            json={"message": "Hello, teach me basic English greetings.", "session_kind": "teacher", "language_code": "en"},
            headers=auth_headers(demo_token),
            timeout=AI_TIMEOUT,
        )
        assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
        d = r.json()
        assert d["reply"] and len(d["reply"]) > 0
        assert d["session_id"]
        assert len(d["messages"]) >= 2
        pytest.teacher_session = d["session_id"]

    def test_ai_chat_teacher_continues_session(self, session, demo_token):
        sid = getattr(pytest, "teacher_session", None)
        if not sid:
            pytest.skip("no prior session")
        r = session.post(
            f"{API}/ai/chat",
            json={"message": "Give me one more example.", "session_kind": "teacher", "language_code": "en", "session_id": sid},
            headers=auth_headers(demo_token),
            timeout=AI_TIMEOUT,
        )
        assert r.status_code == 200
        assert r.json()["session_id"] == sid
        assert len(r.json()["messages"]) >= 4

    def test_ai_chat_practice(self, session, demo_token):
        r = session.post(
            f"{API}/ai/chat",
            json={"message": "Hi!", "session_kind": "practice", "language_code": "en"},
            headers=auth_headers(demo_token),
            timeout=AI_TIMEOUT,
        )
        assert r.status_code == 200, r.text
        assert r.json()["reply"]

    def test_ai_explain_wrong(self, session, demo_token):
        body = {
            "language_code": "en",
            "question_type": "translation",
            "prompt": "Translate: Merhaba",
            "correct_answer": "Hello",
            "user_answer": "Bye",
        }
        r = session.post(f"{API}/ai/explain-wrong", json=body, headers=auth_headers(demo_token), timeout=AI_TIMEOUT)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["explanation"]
        assert d["correction_hint"]
        assert isinstance(d["examples"], list)

    def test_ai_word(self, session, demo_token):
        r = session.post(
            f"{API}/ai/word",
            json={"word": "beautiful", "language_code": "en", "native_language_code": "tr"},
            headers=auth_headers(demo_token),
            timeout=AI_TIMEOUT,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["word"] and d["meaning"] and d["pronunciation"]
        assert isinstance(d["examples"], list)
        assert isinstance(d["synonyms"], list)

    def test_ai_quiz_generate(self, session, demo_token):
        r = session.post(
            f"{API}/ai/quiz/generate",
            json={"language_code": "en", "level_code": "A1", "topic": "greetings", "num_questions": 3},
            headers=auth_headers(demo_token),
            timeout=AI_TIMEOUT,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert isinstance(d["questions"], list) and len(d["questions"]) >= 3
        for q in d["questions"]:
            assert q["type"] and q["prompt"] and q["correct_answer"]

    def test_ai_translate(self, session, demo_token):
        r = session.post(
            f"{API}/ai/translate",
            json={"text": "Hello world", "source_language_code": "en", "target_language_code": "tr"},
            headers=auth_headers(demo_token),
            timeout=AI_TIMEOUT,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["translation"]
        assert d["explanation"]



class TestAdmin:
    def test_admin_users_requires_admin(self, session, demo_token):
        r = session.get(f"{API}/admin/users", headers=auth_headers(demo_token), timeout=15)
        assert r.status_code == 403, f"expected 403 got {r.status_code}"

    def test_admin_users_list(self, session, admin_token):
        r = session.get(f"{API}/admin/users", headers=auth_headers(admin_token), timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_admin_language_crud(self, session, admin_token):
        code = f"zz{uuid.uuid4().hex[:2]}"
        body = {
            "code": code,
            "name": "TestLang",
            "native_name": "TestLang",
            "flag_emoji": "🏳",
            "order_index": 99,
            "is_active": True,
        }
        r = session.post(f"{API}/admin/languages", json=body, headers=auth_headers(admin_token), timeout=15)
        assert r.status_code == 200, r.text
        lang_id = r.json()["id"]



        r2 = session.delete(f"{API}/admin/languages/{lang_id}", headers=auth_headers(admin_token), timeout=15)
        assert r2.status_code == 200

    def test_admin_language_create_forbidden_for_regular(self, session, demo_token):
        body = {"code": "xx", "name": "x", "native_name": "x", "flag_emoji": "🏳", "order_index": 0, "is_active": True}
        r = session.post(f"{API}/admin/languages", json=body, headers=auth_headers(demo_token), timeout=15)
        assert r.status_code == 403



class TestAuthSecurity:
    @pytest.mark.parametrize("path", [
        "/auth/me",
        "/progress/daily-quests",
        "/stats/me",
        "/leaderboard",
        "/languages/en/curriculum",
    ])
    def test_protected_endpoints_reject_unauth(self, session, path):
        r = session.get(f"{API}{path}", timeout=15)
        assert r.status_code in (401, 403), f"{path} returned {r.status_code}"




class TestHeartsGating:

    def _fresh_user(self, session):
        suffix = uuid.uuid4().hex[:8]
        body = {
            "email": f"heart_{suffix}@example.com",
            "username": f"heart_{suffix}",
            "password": "testpass123",
            "full_name": "Heart Test",
            "native_language_code": "en",
        }
        r = session.post(f"{API}/auth/register", json=body, timeout=15)
        assert r.status_code == 200, r.text
        return r.json()["access_token"], r.json()["user"]

    def test_hearts_zero_returns_402_and_regen_still_available(self, session):
        token, user = self._fresh_user(session)
        max_hearts = user["max_hearts"]
        assert max_hearts > 0
        wrong_body = {
            "question_type": "translation",
            "prompt": "test prompt",
            "user_answer": "x",
            "correct_answer": "y",
            "is_correct": False,
            "language_code": "en",
        }

        last_hearts = user["hearts"]
        for i in range(max_hearts):
            r = session.post(f"{API}/progress/answer", json=wrong_body, headers=auth_headers(token), timeout=15)
            assert r.status_code == 200, f"iter {i}: {r.status_code} {r.text}"
            last_hearts = r.json()["hearts"]
        assert last_hearts == 0, f"Expected hearts=0 after draining, got {last_hearts}"


        r2 = session.post(f"{API}/progress/answer", json=wrong_body, headers=auth_headers(token), timeout=15)
        assert r2.status_code == 402, f"Expected 402 after hearts=0, got {r2.status_code} {r2.text}"
        assert "hearts" in r2.text.lower() or "no hearts" in r2.text.lower(), r2.text


        correct_body = dict(wrong_body)
        correct_body["is_correct"] = True
        r3 = session.post(f"{API}/progress/answer", json=correct_body, headers=auth_headers(token), timeout=15)
        assert r3.status_code == 402, f"Even correct answer must be blocked when hearts=0, got {r3.status_code}"

    def test_refill_hearts_restores_and_deducts_gems(self, session):
        token, user = self._fresh_user(session)

        wrong_body = {
            "question_type": "translation", "prompt": "p", "user_answer": "x",
            "correct_answer": "y", "is_correct": False, "language_code": "en",
        }
        for _ in range(user["max_hearts"]):
            session.post(f"{API}/progress/answer", json=wrong_body, headers=auth_headers(token), timeout=15)
        me = session.get(f"{API}/auth/me", headers=auth_headers(token), timeout=15).json()
        gems_before = me["gems"]
        hearts_missing = me["max_hearts"] - me["hearts"]
        expected_cost = hearts_missing * 10
        r = session.post(f"{API}/users/me/refill-hearts", headers=auth_headers(token), timeout=15)
        if r.status_code == 400:

            assert gems_before < expected_cost, f"unexpected 400: gems={gems_before}, cost={expected_cost}"
            return
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["hearts"] == d["max_hearts"]
        assert d["gems"] == gems_before - expected_cost, f"Expected gems={gems_before - expected_cost}, got {d['gems']}"


        r2 = session.post(f"{API}/progress/answer", json=wrong_body, headers=auth_headers(token), timeout=15)
        assert r2.status_code == 200, f"After refill, answer should work; got {r2.status_code}"



class TestAIQuizNoLeak:

    @staticmethod
    def _validate(questions: list):
        assert isinstance(questions, list) and len(questions) > 0
        for q in questions:
            qtype = q.get("type")
            prompt = (q.get("prompt") or "").strip()
            ptrans = q.get("prompt_translation")
            correct = (q.get("correct_answer") or "").strip()

            meta_forbidden = ["What is the answer?"]
            for m in meta_forbidden:
                assert m.lower() not in prompt.lower(), f"Meta-text '{m}' found in prompt: {prompt}"


            if correct and len(correct) > 2 and qtype in ("multiple_choice", "translation", "fill_blank", "sentence_complete", "word_ordering"):


                assert correct.lower() not in prompt.lower(), (
                    f"correct_answer leaked in prompt. type={qtype} prompt={prompt!r} correct={correct!r}"
                )

            if qtype == "translation":
                assert ptrans is None, f"translation question must have prompt_translation=null, got {ptrans!r}"

            if qtype in ("word_ordering", "sentence_complete"):
                assert ptrans is None, f"{qtype} question must have prompt_translation=null, got {ptrans!r}"

    def _call_with_retry(self, session, token, payload, retries=2):
        for attempt in range(retries + 1):
            r = session.post(
                f"{API}/ai/quiz/generate", json=payload, headers=auth_headers(token), timeout=AI_TIMEOUT,
            )
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 503) and attempt < retries:
                time.sleep(3 * (attempt + 1))
                continue
            pytest.fail(f"quiz generate failed: {r.status_code} {r.text[:400]}")

    def test_quiz_az_family_translation(self, session, demo_token):
        d = self._call_with_retry(session, demo_token, {
            "language_code": "az", "level_code": "A1", "topic": "family",
            "num_questions": 4, "types": ["translation", "multiple_choice"],
        })
        self._validate(d["questions"])

    def test_quiz_en_greetings_mixed(self, session, demo_token):
        d = self._call_with_retry(session, demo_token, {
            "language_code": "en", "level_code": "A1", "topic": "greetings",
            "num_questions": 4, "types": ["translation", "fill_blank", "word_ordering"],
        })
        self._validate(d["questions"])

    def test_quiz_de_food_translation_only(self, session, demo_token):
        d = self._call_with_retry(session, demo_token, {
            "language_code": "de", "level_code": "A2", "topic": "food",
            "num_questions": 3, "types": ["translation"],
        })

        types_seen = {q.get("type") for q in d["questions"]}
        assert "translation" in types_seen, f"expected translation type, saw {types_seen}"
        self._validate(d["questions"])
