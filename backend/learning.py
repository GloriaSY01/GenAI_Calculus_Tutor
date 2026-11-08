"""Pilot collection API: owned snapshots, idempotent writes, frozen attribution.

Legacy logs remain separate. In a small pilot, serializing short write
transactions makes request replay, exposure counters and event emission atomic
on both SQLite and PostgreSQL. Model calls must stay outside those transactions.
"""
from __future__ import annotations

import copy
import hashlib
import os
import time
from collections import Counter
from contextlib import contextmanager
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import Column, Float, JSON, MetaData, String, Table, create_engine, select, text

from . import config, database, generator, socratic
from .schemas import GradeRequest


router = APIRouter(prefix="/learning", tags=["learning"])
metadata = MetaData()
records = Table(
    "learning_records_v2", metadata,
    Column("id", String(100), primary_key=True),
    Column("kind", String(32), nullable=False, index=True),
    Column("owner", String(64), nullable=False, index=True),
    Column("payload", JSON, nullable=False),
)
events = Table(
    "learning_events_v2", metadata,
    Column("id", String(100), primary_key=True),
    Column("experiment_id", String(100), nullable=False, index=True),
    Column("class_id", String(80), nullable=False, index=True),
    Column("created_at", Float, nullable=False),
    Column("payload", JSON, nullable=False),
)
_local_engine = None


def experiment_id():
    return os.getenv("LEARNING_EXPERIMENT_ID", "pilot-v1")


def engine():
    global _local_engine
    if database.enabled():
        return database.engine()
    if _local_engine is None:
        _local_engine = create_engine(
            "sqlite:///" + str(config.DATA_DIR / "learning.sqlite3"),
            connect_args={"check_same_thread": False, "timeout": 30},
        )
    return _local_engine


def init():
    metadata.create_all(engine())


@contextmanager
def transaction():
    init()
    with engine().connect() as connection:
        if connection.dialect.name == "sqlite":
            connection.exec_driver_sql("BEGIN IMMEDIATE")
        elif connection.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_xact_lock(76002026)"))
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise


def owner(token: str | None):
    if not token or len(token) < 32 or len(token) > 200:
        raise HTTPException(401, "Learning identity is missing")
    return hashlib.sha256(token.encode()).hexdigest()


def get(connection, record_id, kind, identity):
    row = connection.execute(select(records).where(records.c.id == str(record_id))).mappings().first()
    if not row:
        raise HTTPException(404, "Learning record not found")
    if row["owner"] != identity or row["kind"] != kind:
        raise HTTPException(403, "Learning record belongs to another identity")
    if row["payload"].get("experiment_id", experiment_id()) != experiment_id():
        raise HTTPException(409, "Record belongs to a different experiment; reconnect")
    return dict(row["payload"])


def find(connection, record_id):
    return connection.execute(select(records.c.id).where(records.c.id == str(record_id))).first() is not None


def save(connection, record_id, kind, identity, payload):
    values = dict(kind=kind, owner=identity, payload=payload)
    if find(connection, record_id):
        connection.execute(records.update().where(records.c.id == str(record_id)).values(**values))
    else:
        connection.execute(records.insert().values(id=str(record_id), **values))


def emit(connection, event_id, context, event, **payload):
    record = {**context, **payload, "event": event, "schema_version": 2,
              "ts": time.time(), "event_id": str(event_id)}
    connection.execute(events.insert().values(
        id=str(event_id), experiment_id=record["experiment_id"],
        class_id=record["class_id"], created_at=record["ts"], payload=record,
    ))


def context(run):
    return {key: run[key] for key in ("run_id", "student_id", "class_id", "experiment_id")}


@router.get("/config")
def settings():
    return {"experiment_id": experiment_id(), "consent_version": "pilot-v1",
            "classes": config.CLASS_OPTIONS}


class RunStart(BaseModel):
    run_id: UUID
    class_id: str
    consent: bool


@router.post("/start")
def start(req: RunStart, x_learning_token: str | None = Header(default=None)):
    identity = owner(x_learning_token)
    if not req.consent:
        raise HTTPException(400, "Consent is required to record learning")
    if req.class_id not in {item["id"] for item in config.CLASS_OPTIONS}:
        raise HTTPException(400, {"code": "UNKNOWN_CLASS", "message":
            "班级已失效，请重新加载班级列表并选择。 / Class unavailable; reload and select a class."})
    with transaction() as connection:
        if find(connection, req.run_id):
            run = get(connection, req.run_id, "run", identity)
            if run["class_id"] != req.class_id or run["experiment_id"] != experiment_id():
                raise HTTPException(409, "Start a new run for this class or experiment")
        else:
            run = dict(run_id=str(req.run_id), student_id=identity, class_id=req.class_id,
                       experiment_id=experiment_id(), consent_version="pilot-v1",
                       started_at=time.time(), status="active")
            save(connection, req.run_id, "run", identity, run)
            emit(connection, "start:" + str(req.run_id), context(run), "run_started")
    return {**context(run), "status": run["status"], "persistence": engine().dialect.name}


class ExposureCreate(BaseModel):
    run_id: UUID
    exposure_id: UUID
    question_id: str
    mode: Literal["free", "challenge"] = "free"
    presented: bool = True


@router.post("/exposures")
def expose(req: ExposureCreate, x_learning_token: str | None = Header(default=None)):
    identity = owner(x_learning_token)
    with transaction() as connection:
        run = get(connection, req.run_id, "run", identity)
        if find(connection, req.exposure_id):
            exposure = get(connection, req.exposure_id, "exposure", identity)
            if any(exposure[key] != str(getattr(req, key)) for key in ("run_id", "question_id", "mode")):
                raise HTTPException(409, "Exposure identity cannot change")
        else:
            question = generator.get(req.question_id)
            if question is None and database.enabled():
                question = database.load_generated_question(req.question_id)
            if question is None:
                raise HTTPException(404, "Question expired; generate a new question")
            exposure = {**context(run), "exposure_id": str(req.exposure_id), "question_id": req.question_id,
                        "mode": req.mode, "question": copy.deepcopy(question), "presented_at": None,
                        "attempt_count": 0, "reply_ids": [], "displayed_reply_ids": []}
            save(connection, req.exposure_id, "exposure", identity, exposure)
            emit(connection, "assigned:" + str(req.exposure_id), context(run), "question_assigned",
                 exposure_id=str(req.exposure_id), question_id=req.question_id, mode=req.mode,
                 section_id=question.get("section_id"), topic=question.get("topic"))
        if req.presented and exposure["presented_at"] is None:
            exposure["presented_at"] = time.time()
            save(connection, req.exposure_id, "exposure", identity, exposure)
            emit(connection, "present:" + str(req.exposure_id), context(run), "question_presented",
                 exposure_id=str(req.exposure_id), question_id=req.question_id, mode=req.mode)
    return {"exposure_id": str(req.exposure_id)}


class AttemptCreate(BaseModel):
    exposure_id: UUID
    attempt_id: UUID
    answer: dict


def validate_answer_shape(answer, question, partial=False):
    key = {"single_choice": "single", "multiple_choice": "multiple",
           "fill_blank": "blanks", "drag_order": "order"}[question["type"]]
    if partial and not answer:
        return
    if set(answer) != {key}:
        raise HTTPException(422, "Answer fields do not match the question type")
    value = answer[key]
    if key == "single":
        valid = type(value) is int and 0 <= value < len(question["options"])
    elif key == "multiple":
        valid = (type(value) is list and all(type(v) is int and 0 <= v < len(question["options"]) for v in value)
                 and len(set(value)) == len(value))
    else:
        valid = type(value) is list and all(type(v) is str and len(v) <= 10000 for v in value)
        if valid and key == "blanks":
            valid = len(value) <= len(question["blank_answers"])
        elif valid:
            valid = not (Counter(value) - Counter(question["steps_correct"]))
    if not valid:
        raise HTTPException(422, "Answer has an invalid type or value")


@router.post("/attempts")
def submit(req: AttemptCreate, x_learning_token: str | None = Header(default=None)):
    identity = owner(x_learning_token)
    with transaction() as connection:
        return submit_in_transaction(connection, req, identity)


def submit_in_transaction(connection, req, identity, challenge=False):
    exposure = get(connection, req.exposure_id, "exposure", identity)
    if find(connection, req.attempt_id):
        attempt = get(connection, req.attempt_id, "attempt", identity)
        if attempt["exposure_id"] != str(req.exposure_id) or attempt["answer"] != req.answer:
            raise HTTPException(409, "An attempt cannot be reused with a different answer")
        return attempt["result"]
    if exposure["mode"] == "challenge" and not challenge:
        raise HTTPException(409, "Submit the complete challenge together")
    if exposure.get("challenge_submitted"):
        raise HTTPException(409, "This challenge answer is locked")
    if exposure["presented_at"] is None:
        raise HTTPException(409, "Display the question before answering")
    question = copy.deepcopy(exposure["question"])
    validate_answer_shape(req.answer, question)
    try:
        answer = GradeRequest(question_id=exposure["question_id"], **{
            key: value for key, value in req.answer.items() if key in {"single", "multiple", "blanks", "order"}
        })
    except ValidationError:
        raise HTTPException(422, "Invalid answer format")
    question["attempts"] = exposure["attempt_count"]
    required = {"single_choice": "single", "multiple_choice": "multiple",
                "fill_blank": "blanks", "drag_order": "order"}[question["type"]]
    if getattr(answer, required) is None or getattr(answer, required) == []:
        raise HTTPException(422, "An answer is required")
    if question["type"] in {"single_choice", "multiple_choice"}:
        chosen = [answer.single] if question["type"] == "single_choice" else answer.multiple
        if any(index < 0 or index >= len(question["options"]) for index in chosen):
            raise HTTPException(422, "Choice index out of range")
    elif question["type"] == "fill_blank":
        if len(answer.blanks) != len(question["blank_answers"]) or any(not value.strip() for value in answer.blanks):
            raise HTTPException(422, "Fill every blank")
    elif Counter(answer.order) != Counter(question["steps_correct"]):
        raise HTTPException(422, "Submit each ordering step exactly once")
    result = generator.grade(answer, record=question).model_dump()
    status = "received" if exposure["displayed_reply_ids"] else "unknown" if exposure["reply_ids"] else "none"
    result.update(attempt_id=str(req.attempt_id), attempt_no=exposure["attempt_count"] + 1,
                  assistance_status=status)
    attempt = {**context(exposure), "exposure_id": str(req.exposure_id),
               "attempt_id": str(req.attempt_id), "answer": req.answer,
               "attempt_no": exposure["attempt_count"] + 1, "result": result,
               "submitted_at": time.time(), "assistance_status": status}
    exposure["attempt_count"] += 1
    save(connection, req.exposure_id, "exposure", identity, exposure)
    save(connection, req.attempt_id, "attempt", identity, attempt)
    emit(connection, req.attempt_id, context(exposure), "practice_grade",
         exposure_id=str(req.exposure_id), attempt_id=str(req.attempt_id),
         question_id=exposure["question_id"], mode=exposure["mode"],
         topic=question.get("topic"), section_id=question.get("section_id"),
         difficulty=question.get("difficulty"), type=question["type"],
         source=question.get("source"), language=question.get("language"),
         generation_method=question.get("generation_method", "legacy_model_or_bank"),
         answer=req.answer, attempts=attempt["attempt_no"], attempt_no=attempt["attempt_no"], correct=result["correct"],
         assistance_status=status, grader_version="rules-v3",
         elapsed_ms=int((time.time() - exposure["presented_at"]) * 1000))
    return result


class ChallengeEntry(BaseModel):
    exposure_id: UUID
    attempt_id: UUID
    answer: dict | None = None
    draft_answer: dict | None = None


class ChallengeSubmit(BaseModel):
    run_id: UUID
    submission_id: UUID
    entries: list[ChallengeEntry] = Field(min_length=1, max_length=100)


@router.post("/challenges")
def submit_challenge(req: ChallengeSubmit, x_learning_token: str | None = Header(default=None)):
    identity = owner(x_learning_token)
    payload = req.model_dump(mode="json")
    with transaction() as connection:
        run = get(connection, req.run_id, "run", identity)
        if find(connection, req.submission_id):
            saved = get(connection, req.submission_id, "challenge", identity)
            if ChallengeSubmit.model_validate(saved["request"]).model_dump(mode="json") != payload:
                raise HTTPException(409, "Challenge submission is immutable")
            return saved["result"]
        if len({e.exposure_id for e in req.entries}) != len(req.entries):
            raise HTTPException(422, "Duplicate question in challenge")
        results = []
        for entry in req.entries:
            exposure = get(connection, entry.exposure_id, "exposure", identity)
            if exposure["run_id"] != str(req.run_id) or exposure["mode"] != "challenge":
                raise HTTPException(409, "Challenge exposure does not match run")
            if exposure.get("challenge_submitted"):
                raise HTTPException(409, "Challenge already submitted")
            if entry.answer is not None and entry.draft_answer is not None:
                raise HTTPException(422, "Submit either an answer or an incomplete draft")
            draft = entry.draft_answer or {}
            if draft:
                validate_answer_shape(draft, exposure["question"], partial=True)
                question = exposure["question"]
                complete = (
                    "single" in draft
                    or bool(draft.get("multiple"))
                    or ("blanks" in draft and len(draft["blanks"]) == len(question.get("blank_answers", []))
                        and all(value.strip() for value in draft["blanks"]))
                    or ("order" in draft and Counter(draft["order"]) == Counter(question.get("steps_correct", [])))
                )
                if complete:
                    raise HTTPException(422, "Complete answers must be submitted for grading")
                if exposure["presented_at"] is None:
                    raise HTTPException(409, "Display the question before entering a draft")
            result = submit_in_transaction(connection, AttemptCreate(
                exposure_id=entry.exposure_id, attempt_id=entry.attempt_id, answer=entry.answer,
            ), identity, challenge=True) if entry.answer is not None else None
            exposure = get(connection, entry.exposure_id, "exposure", identity)
            exposure["challenge_submitted"] = str(req.submission_id)
            if result is None:
                exposure["unsubmitted_answer"] = draft
            save(connection, entry.exposure_id, "exposure", identity, exposure)
            if result is None:
                emit(connection, "skip:" + str(entry.exposure_id), context(run), "question_skipped",
                     exposure_id=str(entry.exposure_id), presented=exposure["presented_at"] is not None,
                     draft_answer=draft, reason="incomplete" if any(
                         (isinstance(value, list) and any(str(v).strip() for v in value))
                         or (not isinstance(value, list) and value is not None) for value in draft.values()
                     ) else "unanswered")
            results.append(result)
        result = {"results": results, "submission_id": str(req.submission_id)}
        save(connection, req.submission_id, "challenge", identity, {"request": payload, "result": result})
        emit(connection, "challenge:" + str(req.submission_id), context(run), "challenge_submitted",
             submission_id=str(req.submission_id), assigned=len(results), answered=sum(r is not None for r in results))
        return result


class TutorRequest(BaseModel):
    run_id: UUID
    exposure_id: UUID | None = None
    request_id: UUID
    submitted_attempt_id: UUID | None = None
    text: str = Field(min_length=1, max_length=10000)
    topic: str = Field(default="Calculus 1", max_length=300)
    language: Literal["zh", "en"] = "en"


@router.post("/tutor")
def tutor(req: TutorRequest, x_learning_token: str | None = Header(default=None)):
    identity = owner(x_learning_token)
    session_id = "dialog:" + str(req.exposure_id or req.run_id)
    with transaction() as connection:
        run = get(connection, req.run_id, "run", identity)
        exposure = get(connection, req.exposure_id, "exposure", identity) if req.exposure_id else None
        if exposure and exposure["run_id"] != str(req.run_id):
            raise HTTPException(403, "Run does not own this exposure")
        if exposure and exposure["presented_at"] is None:
            raise HTTPException(409, "Display the question before requesting help")
        if exposure and exposure["mode"] == "challenge" and not exposure.get("challenge_submitted"):
            raise HTTPException(409, "The tutor opens after challenge submission")
        submitted = None
        if req.submitted_attempt_id:
            submitted = get(connection, req.submitted_attempt_id, "attempt", identity)
            if not exposure or submitted["exposure_id"] != str(req.exposure_id):
                raise HTTPException(403, "Submitted answer belongs to another question exposure")
        if find(connection, req.request_id):
            existing = get(connection, req.request_id, "reply", identity)
            if TutorRequest.model_validate(existing["request"]).model_dump(mode="json") != req.model_dump(mode="json"):
                raise HTTPException(409, "Request ID already used")
            if existing.get("result"):
                return existing["result"]
            if existing.get("failed") or time.time() - existing["started_at"] > 300:
                raise HTTPException(503, {"message": "Tutor request failed; please send again", "code": "TUTOR_FAILED"})
            raise HTTPException(409, "Tutor request is still processing")
        session = get(connection, session_id, "dialog", identity) if find(connection, session_id) else {
            "history": [], "hint_level": 0, "mastery": 0, "turns": 0, "pending": None,
        }
        if session.get("pending"):
            pending = get(connection, session["pending"], "reply", identity)
            if time.time() - pending["started_at"] <= 300:
                raise HTTPException(409, "Wait for the previous reply")
            pending["failed"] = True
            save(connection, session["pending"], "reply", identity, pending)
        session["pending"] = str(req.request_id)
        save(connection, session_id, "dialog", identity, session)
        reply = {"request": req.model_dump(mode="json"), "result": None, "started_at": time.time()}
        save(connection, req.request_id, "reply", identity, reply)
        if exposure:
            exposure["reply_ids"].append(str(req.request_id))
            save(connection, req.exposure_id, "exposure", identity, exposure)
        emit(connection, "request:" + str(req.request_id), context(run), "tutor_requested",
             exposure_id=str(req.exposure_id) if exposure else None, student_text=req.text,
             submitted_attempt_id=str(req.submitted_attempt_id) if submitted else None)
    try:
        problem = None
        if exposure:
            question = exposure["question"]
            problem = generator.to_problem(question["id"], record=question)
        turn = socratic.process_turn(
            problem=problem, condition="explain", history=list(session["history"]),
            hint_level=session["hint_level"], mastery=session["mastery"],
            student_text=req.text, current_topic=req.topic, language=req.language,
            prior_answer=submitted["answer"] if submitted else None,
        )
        result = {**turn.model_dump(), "reply_id": str(req.request_id)}
    except Exception:
        with transaction() as connection:
            current = get(connection, session_id, "dialog", identity)
            if current["pending"] == str(req.request_id):
                current["pending"] = None
                save(connection, session_id, "dialog", identity, current)
                reply["failed"] = True
                save(connection, req.request_id, "reply", identity, reply)
                emit(connection, "failed:" + str(req.request_id), context(run), "tutor_failed",
                     exposure_id=str(req.exposure_id) if exposure else None)
        raise HTTPException(503, {"message": "Tutor unavailable; please send again", "code": "TUTOR_FAILED"})
    with transaction() as connection:
        current = get(connection, session_id, "dialog", identity)
        if current["pending"] != str(req.request_id):
            raise HTTPException(409, "Tutor request expired")
        session["history"].extend([{"role": "user", "content": req.text},
                                   {"role": "assistant", "content": turn.tutor_message}])
        session.update(hint_level=turn.hint_level, mastery=turn.mastery,
                       turns=session["turns"] + 1, pending=None)
        save(connection, session_id, "dialog", identity, session)
        reply["result"] = result
        save(connection, req.request_id, "reply", identity, reply)
        if session["turns"] == 1:
            emit(connection, session_id, context(run), "session_start", session_id=session_id,
                 topic=problem.topic if problem else req.topic, problem_id=problem.id if problem else "free")
        emit(connection, "turn:" + str(req.request_id), context(run), "turn", session_id=session_id,
             exposure_id=str(req.exposure_id) if exposure else None,
             submitted_attempt_id=str(req.submitted_attempt_id) if submitted else None,
             topic=problem.topic if problem else req.topic,
             student_text=req.text, turn_index=session["turns"], **result)
    return result


@router.post("/replies/{reply_id}/presented")
def presented(reply_id: UUID, x_learning_token: str | None = Header(default=None)):
    identity = owner(x_learning_token)
    with transaction() as connection:
        reply = get(connection, reply_id, "reply", identity)
        if not reply.get("result"):
            raise HTTPException(409, "Reply not ready")
        exposure_id = reply["request"].get("exposure_id")
        if not reply.get("presented_at"):
            run = get(connection, reply["request"]["run_id"], "run", identity)
            exposure = get(connection, exposure_id, "exposure", identity) if exposure_id else None
            if exposure and reply["result"].get("response_status", "ok") == "ok" and not reply["result"].get("safety_event") and reply["result"].get("action") != "blocked":
                exposure["displayed_reply_ids"].append(str(reply_id))
                save(connection, exposure_id, "exposure", identity, exposure)
            reply["presented_at"] = time.time()
            save(connection, reply_id, "reply", identity, reply)
            emit(connection, "shown:" + str(reply_id), context(run), "tutor_response_presented",
                 exposure_id=exposure_id, reply_id=str(reply_id))
    return {"saved": True}


def list_events(class_id=None):
    init()
    statement = select(events.c.payload).where(events.c.experiment_id == experiment_id())
    if class_id:
        statement = statement.where(events.c.class_id == class_id)
    with engine().connect() as connection:
        return [dict(row[0]) for row in connection.execute(statement.order_by(events.c.created_at, events.c.id))]
