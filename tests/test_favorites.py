import json

from fastapi.testclient import TestClient

from backend import config, generator
from backend.main import app


def _configure_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "FAVORITES_FILE", tmp_path / "favorites.json")
    monkeypatch.setattr(config, "LOG_DIR", tmp_path / "logs")
    config.LOG_DIR.mkdir()


def _register_question():
    generator._REGISTRY["favorite_q"] = {
        "id": "favorite_q",
        "type": "single_choice",
        "topic": "3.1 Defining the Derivative",
        "difficulty": "medium",
        "stem": "What does the derivative represent?",
        "instructions": "Select the one correct answer.",
        "options": ["A rate of change", "An area"],
        "correct_indices": [0],
        "final_answer": "A rate of change",
        "explanation": "Secret explanation",
        "attempts": 0,
    }


def test_favorite_api_persists_public_snapshot(monkeypatch, tmp_path):
    _configure_paths(monkeypatch, tmp_path)
    _register_question()
    client = TestClient(app)

    payload = {
        "student_id": "alice",
        "class_id": "calc1-a",
        "question_id": "favorite_q",
    }
    response = client.post("/favorites", json=payload)
    assert response.status_code == 200
    assert response.json()["stem"] == "What does the derivative represent?"

    # Upsert semantics keep one record and do not expose answer material.
    assert client.post("/favorites", json=payload).status_code == 200
    saved = client.get("/favorites", params={"student_id": "alice"}).json()
    assert len(saved) == 1
    raw = (tmp_path / "favorites.json").read_text(encoding="utf-8")
    assert "Secret explanation" not in raw
    assert "final_answer" not in raw

    events = [
        json.loads(line)
        for line in (tmp_path / "logs" / "practice.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert [event["event"] for event in events] == ["favorite_add"]


def test_favorite_api_removes_record(monkeypatch, tmp_path):
    _configure_paths(monkeypatch, tmp_path)
    _register_question()
    client = TestClient(app)
    payload = {
        "student_id": "alice",
        "class_id": "calc1-a",
        "question_id": "favorite_q",
    }
    client.post("/favorites", json=payload)

    response = client.delete(
        "/favorites/favorite_q", params={"student_id": "alice"}
    )
    assert response.status_code == 200
    assert client.get("/favorites", params={"student_id": "alice"}).json() == []


def test_anonymous_student_cannot_create_favorite(monkeypatch, tmp_path):
    _configure_paths(monkeypatch, tmp_path)
    _register_question()
    client = TestClient(app)

    response = client.post(
        "/favorites",
        json={
            "student_id": "anon",
            "class_id": "demo",
            "question_id": "favorite_q",
        },
    )
    assert response.status_code == 400
