"""Simple JSON-backed assignment store (teacher assigns practice to the class).

This is intentionally minimal: assignments are persisted to
data/assignments.json so the teacher view can create and list them across
restarts, without pulling in a database for the demo.
"""
import json
import time
import uuid
from typing import List

from . import config
from .schemas import Assignment, AssignmentCreate


def _read_all() -> List[dict]:
    if not config.ASSIGNMENTS_FILE.exists():
        return []
    try:
        with open(config.ASSIGNMENTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _write_all(items: List[dict]) -> None:
    config.ASSIGNMENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(config.ASSIGNMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def _upgrade(record: dict) -> dict:
    """Convert a legacy single-block record (topic/qtype/n_questions at the top
    level) into the current multi-block `items` shape."""
    if "items" not in record and "qtype" in record:
        record = {
            "id": record.get("id", ""),
            "created_at": record.get("created_at", 0),
            "title": record.get("title", ""),
            "note": record.get("note", ""),
            "items": [{
                "topic": record.get("topic", ""),
                "qtype": record.get("qtype", "single_choice"),
                "difficulty": record.get("difficulty", "medium"),
                "count": record.get("n_questions", 1),
            }],
        }
    return record


def list_assignments() -> List[Assignment]:
    items = _read_all()
    items.sort(key=lambda a: a.get("created_at", 0), reverse=True)
    return [Assignment(**_upgrade(a)) for a in items]


def create_assignment(req: AssignmentCreate) -> Assignment:
    record = Assignment(
        id="asg_" + uuid.uuid4().hex[:8],
        created_at=time.time(),
        **req.model_dump(),
    )
    items = _read_all()
    items.append(record.model_dump())
    _write_all(items)
    return record


def delete_assignment(assignment_id: str) -> bool:
    items = _read_all()
    new_items = [a for a in items if a.get("id") != assignment_id]
    if len(new_items) == len(items):
        return False
    _write_all(new_items)
    return True
