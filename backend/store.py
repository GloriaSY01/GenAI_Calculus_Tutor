"""In-memory session store plus JSONL event logging for later analysis.

Sessions live in memory (fine for a single-process demo). Every turn is also
appended to data/logs/<session_id>.jsonl so the explanation/justification data
can be analysed offline -- this is what feeds the planned empirical study.
"""
import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from . import config
from .schemas import Condition, Language, Problem


@dataclass
class Session:
    session_id: str
    problem: Optional[Problem]
    condition: Condition
    student_id: str
    class_id: Optional[str] = None
    topic: Optional[str] = None
    language: Language = "en"
    history: List[Dict[str, str]] = field(default_factory=list)
    hint_level: int = 0
    mastery: int = 0
    turns: int = 0
    is_solved: bool = False
    created_at: float = field(default_factory=time.time)
    last_activity_at: float = field(default_factory=time.time)
    recent_student_texts: List[str] = field(default_factory=list)
    hint_request_streak: int = 0


_SESSIONS: Dict[str, Session] = {}
_FAVORITES_LOCK = threading.RLock()


def create_session(problem: Optional[Problem], condition: Condition,
                   student_id: str, topic: Optional[str] = None,
                   class_id: Optional[str] = None,
                   language: Language = "en") -> Session:
    sid = uuid.uuid4().hex[:12]
    session = Session(
        session_id=sid, problem=problem, condition=condition,
        student_id=student_id or "anon", class_id=class_id,
        topic=(problem.section_id or problem.topic) if problem else topic,
        language=language,
    )
    _SESSIONS[sid] = session
    _log(session, {"event": "session_start",
                   "problem_id": problem.id if problem else "free",
                   "condition": condition, "topic": session.topic,
                   "language": session.language})
    return session


def get_session(session_id: str) -> Session | None:
    return _SESSIONS.get(session_id)


def log_turn(session: Session, student_text: str, turn_payload: dict,
             latency_ms: int, response_time_ms: int | None = None) -> None:
    _log(session, {
        "event": "turn",
        "turn_index": session.turns,
        "student_text": student_text,
        "language": session.language,
        "latency_ms": latency_ms,
        "response_time_ms": response_time_ms,
        **turn_payload,
    })


def log_practice(payload: dict) -> None:
    """Append privacy-minimal practice events to a shared JSONL stream."""
    log_activity("practice_grade", payload)


def log_activity(event: str, payload: dict) -> None:
    """Append a student activity event to the shared JSONL stream."""
    record = {"ts": time.time(), "event": event, **payload}
    path = config.LOG_DIR / "practice.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def list_favorites(student_id: str) -> List[dict]:
    """Return one student's favorites, newest first."""
    with _FAVORITES_LOCK:
        records = _read_favorites().get(student_id, [])
    return sorted(records, key=lambda item: item.get("saved_at", 0), reverse=True)


def add_favorite(record: dict) -> dict:
    """Upsert a question snapshot in one student's favorites."""
    student_id = record["student_id"]
    with _FAVORITES_LOCK:
        data = _read_favorites()
        favorites = data.setdefault(student_id, [])
        existing = next(
            (item for item in favorites if item["question_id"] == record["question_id"]),
            None,
        )
        if existing is not None:
            return existing
        favorites.append(record)
        _write_favorites(data)
    log_activity("favorite_add", {
        "student_id": student_id,
        "class_id": record["class_id"],
        "question_id": record["question_id"],
        "topic": record["topic"],
    })
    return record


def remove_favorite(student_id: str, question_id: str) -> bool:
    """Remove a favorite and return whether it existed."""
    removed = None
    with _FAVORITES_LOCK:
        data = _read_favorites()
        favorites = data.get(student_id, [])
        kept = []
        for item in favorites:
            if item["question_id"] == question_id and removed is None:
                removed = item
            else:
                kept.append(item)
        if removed is None:
            return False
        if kept:
            data[student_id] = kept
        else:
            data.pop(student_id, None)
        _write_favorites(data)
    log_activity("favorite_remove", {
        "student_id": student_id,
        "class_id": removed.get("class_id"),
        "question_id": question_id,
        "topic": removed.get("topic"),
    })
    return True


def _read_favorites() -> Dict[str, List[dict]]:
    if not config.FAVORITES_FILE.exists():
        return {}
    with open(config.FAVORITES_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def _write_favorites(data: Dict[str, List[dict]]) -> None:
    config.FAVORITES_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_path = config.FAVORITES_FILE.with_suffix(".json.tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    temp_path.replace(config.FAVORITES_FILE)


def _log(session: Session, payload: dict) -> None:
    record = {
        "ts": time.time(),
        "session_id": session.session_id,
        "student_id": session.student_id,
        "class_id": session.class_id,
        **payload,
    }
    path = config.LOG_DIR / f"{session.session_id}.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
