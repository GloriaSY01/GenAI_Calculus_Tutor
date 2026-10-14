"""Optional PostgreSQL persistence for shared deployments.

Local development keeps using the existing JSON files when DATABASE_URL is
unset. Railway supplies DATABASE_URL when a PostgreSQL service is attached.
"""
from __future__ import annotations

import os
import time
from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    and_,
    create_engine,
    delete,
    select,
)
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.engine import Engine


metadata = MetaData()

favorites = Table(
    "favorites",
    metadata,
    Column("student_id", String(160), primary_key=True),
    Column("question_id", String(160), primary_key=True),
    Column("class_id", String(80), nullable=True, index=True),
    Column("snapshot", JSON, nullable=False),
    Column("saved_at", Float, nullable=False, index=True),
)

assignments = Table(
    "assignments",
    metadata,
    Column("id", String(80), primary_key=True),
    Column("class_id", String(80), nullable=True, index=True),
    Column("title", Text, nullable=False),
    Column("note", Text, nullable=False, default=""),
    Column("items", JSON, nullable=False),
    Column("created_at", Float, nullable=False, index=True),
)

learning_events = Table(
    "learning_events",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("session_id", String(80), nullable=True, index=True),
    Column("student_id", String(160), nullable=True, index=True),
    Column("class_id", String(80), nullable=True, index=True),
    Column("event", String(80), nullable=False, index=True),
    Column("topic", String(240), nullable=True, index=True),
    Column("payload", JSON, nullable=False),
    Column("created_at", Float, nullable=False, index=True),
)

tutor_sessions = Table(
    "tutor_sessions",
    metadata,
    Column("id", String(80), primary_key=True),
    Column("student_id", String(160), nullable=True, index=True),
    Column("class_id", String(80), nullable=True, index=True),
    Column("state", JSON, nullable=False),
    Column("updated_at", Float, nullable=False),
)

generated_questions = Table(
    "generated_questions",
    metadata,
    Column("question_id", String(160), primary_key=True),
    Column("record", JSON, nullable=False),
    Column("created_at", Float, nullable=False, index=True),
)

student_progress = Table(
    "student_progress",
    metadata,
    Column("student_id", String(160), primary_key=True),
    Column("class_id", String(80), primary_key=True),
    Column("scope", String(120), primary_key=True),
    Column("version", Integer, nullable=False),
    Column("state", JSON, nullable=False),
    Column("updated_at", Float, nullable=False),
)

_engine: Engine | None = None


def enabled() -> bool:
    return bool(os.getenv("DATABASE_URL", "").strip())


def _url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def engine() -> Engine:
    global _engine
    if _engine is None:
        if not enabled():
            raise RuntimeError("DATABASE_URL is not configured")
        kwargs: dict[str, Any] = {"pool_pre_ping": True}
        if _url().startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
        _engine = create_engine(_url(), **kwargs)
    return _engine


def init() -> None:
    if enabled():
        metadata.create_all(engine())


def _upsert(table: Table, values: dict, key_columns: list[str]) -> None:
    eng = engine()
    with eng.begin() as connection:
        if eng.dialect.name == "postgresql":
            statement = postgres_insert(table).values(**values)
            updates = {key: value for key, value in values.items() if key not in key_columns}
            connection.execute(
                statement.on_conflict_do_update(
                    index_elements=[table.c[key] for key in key_columns],
                    set_=updates,
                )
            )
            return
        where = and_(*(table.c[key] == values[key] for key in key_columns))
        connection.execute(delete(table).where(where))
        connection.execute(table.insert().values(**values))


def list_favorites(student_id: str) -> list[dict]:
    statement = (
        select(favorites.c.snapshot)
        .where(favorites.c.student_id == student_id)
        .order_by(favorites.c.saved_at.desc())
    )
    with engine().connect() as connection:
        return [dict(row[0]) for row in connection.execute(statement)]


def add_favorite(record: dict) -> dict:
    _upsert(
        favorites,
        {
            "student_id": record["student_id"],
            "question_id": record["question_id"],
            "class_id": record.get("class_id"),
            "snapshot": record,
            "saved_at": float(record.get("saved_at", time.time())),
        },
        ["student_id", "question_id"],
    )
    return record


def remove_favorite(student_id: str, question_id: str) -> bool:
    with engine().begin() as connection:
        result = connection.execute(
            delete(favorites).where(
                and_(
                    favorites.c.student_id == student_id,
                    favorites.c.question_id == question_id,
                )
            )
        )
        return bool(result.rowcount)


def list_assignments(class_id: str | None = None) -> list[dict]:
    statement = select(assignments)
    if class_id:
        statement = statement.where(assignments.c.class_id == class_id)
    statement = statement.order_by(assignments.c.created_at.desc())
    with engine().connect() as connection:
        return [dict(row._mapping) for row in connection.execute(statement)]


def add_assignment(record: dict) -> dict:
    _upsert(assignments, record, ["id"])
    return record


def remove_assignment(assignment_id: str) -> bool:
    with engine().begin() as connection:
        result = connection.execute(
            delete(assignments).where(assignments.c.id == assignment_id)
        )
        return bool(result.rowcount)


def add_event(record: dict) -> None:
    with engine().begin() as connection:
        connection.execute(
            learning_events.insert().values(
                session_id=record.get("session_id"),
                student_id=record.get("student_id"),
                class_id=record.get("class_id"),
                event=record.get("event", "activity"),
                topic=record.get("section_id") or record.get("topic"),
                payload=record,
                created_at=float(record.get("ts", time.time())),
            )
        )


def list_events() -> list[dict]:
    with engine().connect() as connection:
        rows = connection.execute(
            select(learning_events.c.payload).order_by(learning_events.c.created_at)
        )
        return [dict(row[0]) for row in rows]


def save_session(session_id: str, student_id: str, class_id: str | None, state: dict) -> None:
    _upsert(
        tutor_sessions,
        {
            "id": session_id,
            "student_id": student_id,
            "class_id": class_id,
            "state": state,
            "updated_at": time.time(),
        },
        ["id"],
    )


def load_session(session_id: str) -> dict | None:
    with engine().connect() as connection:
        row = connection.execute(
            select(tutor_sessions.c.state).where(tutor_sessions.c.id == session_id)
        ).first()
        return dict(row[0]) if row else None


def save_generated_question(record: dict) -> None:
    _upsert(
        generated_questions,
        {
            "question_id": record["id"],
            "record": record,
            "created_at": float(record.get("created_at", time.time())),
        },
        ["question_id"],
    )


def load_generated_questions(limit: int = 2000) -> dict[str, dict]:
    statement = (
        select(generated_questions.c.question_id, generated_questions.c.record)
        .order_by(generated_questions.c.created_at.desc())
        .limit(limit)
    )
    with engine().connect() as connection:
        return {row[0]: dict(row[1]) for row in connection.execute(statement)}


def get_progress(student_id: str, class_id: str, scope: str) -> dict | None:
    statement = select(
        student_progress.c.version,
        student_progress.c.state,
        student_progress.c.updated_at,
    ).where(
        and_(
            student_progress.c.student_id == student_id,
            student_progress.c.class_id == class_id,
            student_progress.c.scope == scope,
        )
    )
    with engine().connect() as connection:
        row = connection.execute(statement).first()
        if not row:
            return None
        return {"version": row[0], "state": row[1], "updated_at": row[2]}


def save_progress(
    student_id: str,
    class_id: str,
    scope: str,
    version: int,
    state: dict,
) -> dict:
    updated_at = time.time()
    _upsert(
        student_progress,
        {
            "student_id": student_id,
            "class_id": class_id,
            "scope": scope,
            "version": version,
            "state": state,
            "updated_at": updated_at,
        },
        ["student_id", "class_id", "scope"],
    )
    return {"version": version, "state": state, "updated_at": updated_at}
