import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().strip('"').rstrip("/")


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": "demo@cookielearn.app", "password": "demo123"}, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.mark.parametrize("i", list(range(6)))
def test_quiz_generate_stress_en_greetings(token, i):
    r = requests.post(
        f"{BASE_URL}/api/ai/quiz/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"language_code": "en", "level_code": "A1", "topic": "greetings",
              "num_questions": 4, "types": ["translation", "fill_blank", "word_ordering"]},
        timeout=90,
    )
    assert r.status_code in (200, 502), f"iter {i}: unexpected {r.status_code} - {r.text[:400]}"
    if r.status_code == 200:
        data = r.json()
        assert len(data["questions"]) >= 1
        for q in data["questions"]:
            assert q.get("prompt")
            assert q.get("correct_answer")
            assert q.get("type")


@pytest.mark.parametrize("i", list(range(6)))
def test_quiz_generate_stress_az_family(token, i):
    r = requests.post(
        f"{BASE_URL}/api/ai/quiz/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"language_code": "az", "level_code": "A1", "topic": "family",
              "num_questions": 4, "types": ["translation"]},
        timeout=90,
    )
    assert r.status_code in (200, 502), f"iter {i}: unexpected {r.status_code} - {r.text[:400]}"
