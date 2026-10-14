from backend import database


def test_shared_persistence_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'shared.sqlite3'}")
    database._engine = None
    database.init()

    favorite = {
        "student_id": "alice",
        "question_id": "q1",
        "class_id": "calc1-a",
        "topic": "Derivatives",
        "saved_at": 1.0,
    }
    database.add_favorite(favorite)
    assert database.list_favorites("alice") == [favorite]

    database.add_assignment({
        "id": "a1",
        "class_id": "calc1-a",
        "title": "Week 1",
        "note": "",
        "items": [],
        "created_at": 2.0,
    })
    assert database.list_assignments("calc1-a")[0]["id"] == "a1"

    database.add_event({
        "ts": 3.0,
        "event": "practice_grade",
        "student_id": "alice",
        "class_id": "calc1-a",
        "topic": "Derivatives",
    })
    assert database.list_events()[0]["event"] == "practice_grade"

    database.save_progress("alice", "calc1-a", "study", 3, {"rounds": {}})
    assert database.get_progress("alice", "calc1-a", "study")["version"] == 3

    database.save_session("s1", "alice", "calc1-a", {"session_id": "s1"})
    assert database.load_session("s1")["session_id"] == "s1"

    database.save_generated_question({"id": "q1", "created_at": 4.0, "stem": "x"})
    assert database.load_generated_questions()["q1"]["stem"] == "x"

    database.engine().dispose()
    database._engine = None
