"""In-memory session store plus JSONL event logging for later analysis.

Sessions live in memory (fine for a single-process demo). Every turn is also
appended to data/logs/<session_id>.jsonl so the explanation/justification data
can be analysed offline -- this is what feeds the planned empirical study.
"""
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from . import config
from .schemas import Condition, Problem


@dataclass
class Session:
    session_id: str
    problem: Optional[Problem]
    condition: Condition
    student_id: str
    history: List[Dict[str, str]] = field(default_factory=list)
    hint_level: int = 0
    mastery: int = 0
    turns: int = 0
    is_solved: bool = False
    created_at: float = field(default_factory=time.time)


_SESSIONS: Dict[str, Session] = {}


def create_session(problem: Optional[Problem], condition: Condition,
                   student_id: str) -> Session:
    sid = uuid.uuid4().hex[:12]
    session = Session(
        session_id=sid, problem=problem, condition=condition,
        student_id=student_id or "anon",
    )
    _SESSIONS[sid] = session
    _log(session, {"event": "session_start",
                   "problem_id": problem.id if problem else "free",
                   "condition": condition, "student_id": session.student_id})
    return session


def get_session(session_id: str) -> Session | None:
    return _SESSIONS.get(session_id)


def log_turn(session: Session, student_text: str, turn_payload: dict,
             latency_ms: int) -> None:
    _log(session, {
        "event": "turn",
        "turn_index": session.turns,
        "student_text": student_text,
        "latency_ms": latency_ms,
        **turn_payload,
    })


def _log(session: Session, payload: dict) -> None:
    record = {"ts": time.time(), "session_id": session.session_id, **payload}
    path = config.LOG_DIR / f"{session.session_id}.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
