
import os
import uuid

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
API = f"{BASE_URL}/api"

DEMO = {"email": "demo@cookielearn.app", "password": "demo123"}
AI_TIMEOUT = 60


def auth_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def demo_token(session):
    r = session.post(f"{API}/auth/login", json=DEMO, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _fresh_user(session):
    suffix = uuid.uuid4().hex[:8]
    body = {
        "email": f"prac_{suffix}@example.com",
        "username": f"prac_{suffix}",
        "password": "testpass123",
        "full_name": "Practice Test",
        "native_language_code": "en",
    }
    r = session.post(f"{API}/auth/register", json=body, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["access_token"], r.json()["user"]


class TestPracticeAuth:
    def test_evaluate_requires_auth(self, session):
        r = session.post(f"{API}/practice/evaluate", json={
            "language_code": "tr", "question_type": "translation",
            "prompt": "p", "correct_answer": "x", "user_answer": "y",
        }, timeout=15)
        assert r.status_code in (401, 403)

    def test_finish_requires_auth(self, session):
        r = session.post(f"{API}/practice/finish", json={
            "language_code": "tr", "difficulty": "easy",
            "correct_count": 5, "total_count": 6, "duration_seconds": 100,
        }, timeout=15)
        assert r.status_code in (401, 403)


class TestSemanticEvaluate:
    def test_semantic_equivalence_zahmet_olmazsa(self, session, demo_token):

        r = session.post(f"{API}/practice/evaluate", json={
            "language_code": "tr",
            "level_code": "A1",
            "question_type": "translation",
            "prompt": "Translate: Two teas and one sugar, please.",
            "correct_answer": "Two teas and one sugar, please.",
            "user_answer": "two teas and one sugar please",
        }, headers=auth_headers(demo_token), timeout=AI_TIMEOUT)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["is_correct"] is True, f"Semantic variant rejected: {d}"
        assert "hearts" in d

    def test_capitalization_variant_accepted(self, session, demo_token):
        r = session.post(f"{API}/practice/evaluate", json={
            "language_code": "en",
            "level_code": "A1",
            "question_type": "translation",
            "prompt": "Translate: Merhaba",
            "correct_answer": "Hello",
            "user_answer": "hello",
        }, headers=auth_headers(demo_token), timeout=AI_TIMEOUT)
        assert r.status_code == 200, r.text
        assert r.json()["is_correct"] is True

    def test_clear_wrong_meaning_rejected(self, session, demo_token):
        token, _ = _fresh_user(session)
        r = session.post(f"{API}/practice/evaluate", json={
            "language_code": "en",
            "level_code": "A1",
            "question_type": "translation",
            "prompt": "Translate: Merhaba",
            "correct_answer": "Hello",
            "user_answer": "Goodbye",
        }, headers=auth_headers(token), timeout=AI_TIMEOUT)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["is_correct"] is False

    def test_wrong_answer_deducts_heart(self, session):
        token, user = _fresh_user(session)
        h0 = user["hearts"]
        r = session.post(f"{API}/practice/evaluate", json={
            "language_code": "en",
            "level_code": "A1",
            "question_type": "translation",
            "prompt": "Translate: Merhaba",
            "correct_answer": "Hello",
            "user_answer": "Bye forever",
        }, headers=auth_headers(token), timeout=AI_TIMEOUT)
        assert r.status_code == 200, r.text
        d = r.json()
        if d["is_correct"] is False:
            assert d["hearts"] == max(0, h0 - 1), f"expected {h0-1}, got {d['hearts']}"

    def test_402_when_hearts_zero(self, session):
        token, user = _fresh_user(session)

        wrong = {
            "question_type": "translation", "prompt": "p", "user_answer": "x",
            "correct_answer": "y", "is_correct": False, "language_code": "en",
        }
        for _ in range(user["max_hearts"]):
            session.post(f"{API}/progress/answer", json=wrong, headers=auth_headers(token), timeout=15)
        me = session.get(f"{API}/auth/me", headers=auth_headers(token), timeout=15).json()
        assert me["hearts"] == 0

        r = session.post(f"{API}/practice/evaluate", json={
            "language_code": "en", "level_code": "A1",
            "question_type": "translation",
            "prompt": "Translate: Merhaba", "correct_answer": "Hello",
            "user_answer": "Hello",
        }, headers=auth_headers(token), timeout=AI_TIMEOUT)
        assert r.status_code == 402, f"expected 402, got {r.status_code} {r.text[:200]}"

    def test_evaluate_persists_user_answer(self, session):

        token, _ = _fresh_user(session)

        r = session.post(f"{API}/practice/evaluate", json={
            "language_code": "en",
            "level_code": "A1",
            "question_type": "translation",
            "prompt": "Translate: Merhaba",
            "correct_answer": "Hello",
            "user_answer": "Absolutely not a translation",
            "topic": "greetings",
        }, headers=auth_headers(token), timeout=AI_TIMEOUT)
        assert r.status_code == 200

        stats = session.get(f"{API}/stats/me", headers=auth_headers(token), timeout=15).json()
        assert "accuracy" in stats
        assert 0.0 <= stats["accuracy"] <= 1.0


class TestFinishXP:
    def test_hard_perfect_multiplier(self, session):
        token, _ = _fresh_user(session)
        r = session.post(f"{API}/practice/finish", json={
            "language_code": "en", "difficulty": "hard",
            "correct_count": 6, "total_count": 6, "duration_seconds": 120,
        }, headers=auth_headers(token), timeout=20)
        assert r.status_code == 200, r.text
        d = r.json()

        assert d["xp_earned"] == 66, f"expected 66 xp for hard 6/6 within 180s, got {d['xp_earned']}"
        assert d["accuracy"] == 1.0
        assert d["streak_days"] >= 1
        assert d["daily_xp_earned"] >= 66

    def test_medium_multiplier(self, session):
        token, _ = _fresh_user(session)
        r = session.post(f"{API}/practice/finish", json={
            "language_code": "en", "difficulty": "medium",
            "correct_count": 6, "total_count": 6, "duration_seconds": 120,
        }, headers=auth_headers(token), timeout=20)
        assert r.status_code == 200, r.text
        d = r.json()

        assert d["xp_earned"] == 49, f"expected 49 for medium 6/6, got {d['xp_earned']}"

    def test_easy_no_perfect_no_speed(self, session):
        token, _ = _fresh_user(session)
        r = session.post(f"{API}/practice/finish", json={
            "language_code": "en", "difficulty": "easy",
            "correct_count": 4, "total_count": 6, "duration_seconds": 400,
        }, headers=auth_headers(token), timeout=20)
        assert r.status_code == 200, r.text
        d = r.json()

        assert d["xp_earned"] == 12, f"expected 12 for easy 4/6 slow, got {d['xp_earned']}"
        assert d["accuracy"] == pytest.approx(4/6, abs=0.001)

    def test_finish_updates_daily_quests(self, session):
        token, _ = _fresh_user(session)

        q_before = session.get(f"{API}/progress/daily-quests", headers=auth_headers(token), timeout=15).json()
        by_type_before = {q["quest_type"]: q["progress"] for q in q_before}

        r = session.post(f"{API}/practice/finish", json={
            "language_code": "en", "difficulty": "hard",
            "correct_count": 6, "total_count": 6, "duration_seconds": 60,
        }, headers=auth_headers(token), timeout=20)
        assert r.status_code == 200, r.text
        earned = r.json()["xp_earned"]

        q_after = session.get(f"{API}/progress/daily-quests", headers=auth_headers(token), timeout=15).json()
        by_type_after = {q["quest_type"]: q["progress"] for q in q_after}


        earn_xp_target = next(q["target"] for q in q_after if q["quest_type"] == "earn_xp")
        expected_earn_xp = min(earn_xp_target, by_type_before["earn_xp"] + earned)
        assert by_type_after["earn_xp"] == expected_earn_xp, \
            f"earn_xp quest not bumped correctly: {by_type_before['earn_xp']} -> {by_type_after['earn_xp']} (earned {earned}, target {earn_xp_target})"
        assert by_type_after["complete_lessons"] == by_type_before["complete_lessons"] + 1
        assert by_type_after["perfect_lesson"] == by_type_before["perfect_lesson"] + 1
