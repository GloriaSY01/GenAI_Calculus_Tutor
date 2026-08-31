"""FastAPI application exposing the Socratic tutor.

Endpoints:
  GET  /health                       -> liveness + model info
  GET  /problems                     -> public problem list (no answers)
  POST /session/start                -> create a session, get opening message
  POST /session/{sid}/message        -> send a student message, get tutor turn
  GET  /session/{sid}                -> current session state
"""
import re
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import (
    analytics,
    assignments,
    config,
    generator,
    guardrail,
    learning_path,
    problems,
    rag,
    socratic,
    store,
    textbook,
)
from .schemas import (
    AnalyticsAnswer,
    AnalyticsQuery,
    Assignment,
    AssignmentCreate,
    CatalogResponse,
    ClassAnalytics,
    ClassOption,
    ConceptCard,
    Favorite,
    FavoriteCreate,
    GenerateRequest,
    GeneratedQuestionPublic,
    GradeRequest,
    GradeResponse,
    LearningStep,
    MessageRequest,
    ProblemPublic,
    SessionState,
    StartSessionRequest,
    StartSessionResponse,
    TutorTurn,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        rag.warmup()
    except Exception:
        pass
    yield


app = FastAPI(
    title="GenAI Calculus Tutor", version="0.4.0", lifespan=lifespan
)
app.mount(
    "/textbook-assets",
    StaticFiles(directory=config.TEXTBOOK_ASSETS_DIR, check_dir=False),
    name="textbook-assets",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": config.LLM_MODEL,
        "base_url": config.LLM_BASE_URL,
        "rag": rag.index_status(),
    }


@app.get("/problems", response_model=list[ProblemPublic])
def get_problems():
    return problems.list_problems()


@app.get("/topics", response_model=list[str])
def get_topics():
    return [section["title"] for chapter in textbook.catalog_tree()["chapters"]
            for section in chapter["sections"]]


@app.get("/catalog", response_model=CatalogResponse)
def get_catalog():
    return textbook.catalog_tree()


@app.get("/classes", response_model=list[ClassOption])
def get_classes():
    return config.CLASS_OPTIONS


@app.get("/concept", response_model=ConceptCard)
def get_concept(topic: str):
    try:
        return rag.concept_card(topic)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown section")
    except rag.RAGUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/retrieve")
def retrieve_context(query: str, topic: str | None = None, section_id: str | None = None, k: int = 4):
    """Instructor/debug endpoint; it returns attributed source chunks."""
    try:
        return rag.retrieve(
            query, topic=topic, section_id=section_id, k=max(1, min(k, 8))
        )
    except rag.RAGUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/learning-path", response_model=list[LearningStep])
def get_learning_path():
    """Recommended Calculus 1 topic order for first-time learners."""
    return learning_path.load_path()


# --------------------------------------------------------------------------- #
# Teacher analytics (class-level)
# --------------------------------------------------------------------------- #
@app.get("/analytics/class", response_model=ClassAnalytics)
def get_class_analytics():
    return analytics.compute()


@app.post("/analytics/ask", response_model=AnalyticsAnswer)
def ask_analytics(req: AnalyticsQuery):
    data = analytics.compute()
    answer, llm_available = analytics.answer_question(req.question, data)
    return AnalyticsAnswer(answer=answer, grounded_on=data,
                           llm_available=llm_available)


# --------------------------------------------------------------------------- #
# Assignments (teacher -> class)
# --------------------------------------------------------------------------- #
@app.get("/assignments", response_model=list[Assignment])
def get_assignments():
    return assignments.list_assignments()


@app.post("/assignments", response_model=Assignment)
def create_assignment(req: AssignmentCreate):
    return assignments.create_assignment(req)


@app.delete("/assignments/{assignment_id}")
def delete_assignment(assignment_id: str):
    ok = assignments.delete_assignment(assignment_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Unknown assignment_id")
    return {"deleted": assignment_id}


@app.post("/generate", response_model=GeneratedQuestionPublic)
def generate(req: GenerateRequest):
    try:
        return generator.generate_question(
            req.type, req.topic, req.difficulty, language=req.language
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown section") from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502,
                            detail=f"Generation failed: {exc}") from exc


@app.post("/grade", response_model=GradeResponse)
def grade(req: GradeRequest):
    try:
        question = generator.get(req.question_id)
        result = generator.grade(req)
        store.log_practice({
            "question_id": req.question_id,
            "student_id": (req.student_id or "anon").strip() or "anon",
            "class_id": req.class_id,
            "topic": question.get("topic") if question else None,
            "section_id": question.get("section_id") if question else None,
            "source": question.get("source") if question else None,
            "language": question.get("language") if question else None,
            "correct": result.correct,
            "attempts": result.attempts,
            "answer_revealed": result.answer_revealed,
            "elapsed_ms": (
                int((time.time() - question["created_at"]) * 1000)
                if question and question.get("created_at") else None
            ),
        })
        return result
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown question_id")


@app.post("/session/start", response_model=StartSessionResponse)
def start_session(req: StartSessionRequest):
    problem = None
    if req.problem_id:  # None/empty => free chat with no fixed problem
        problem = (problems.get_problem(req.problem_id)
                   or generator.to_problem(req.problem_id))
        if problem is None:
            raise HTTPException(status_code=404, detail="Unknown problem_id")

    session = store.create_session(
        problem,
        req.condition,
        req.student_id or "anon",
        topic=req.topic,
        class_id=req.class_id,
        language=req.language,
    )
    opening = socratic.opening_message(problem, req.condition, req.language)
    session.history.append({"role": "assistant", "content": opening})

    return StartSessionResponse(
        session_id=session.session_id,
        problem=problems.to_public(problem) if problem else None,
        condition=session.condition,
        opening_message=opening,
    )


@app.post("/session/{session_id}/message", response_model=TutorTurn)
def send_message(session_id: str, req: MessageRequest):
    session = store.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown session_id")
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Empty message")
    if req.language:
        session.language = req.language

    response_time_ms = int((time.time() - session.last_activity_at) * 1000)
    asks_hint = bool(re.search(r"hint|提示|不会|不知道|下一步", req.text, re.I))
    hint_streak = session.hint_request_streak + 1 if asks_hint else 0
    engagement_flag = guardrail.engagement_signal(
        req.text,
        elapsed_seconds=response_time_ms / 1000,
        recent_texts=session.recent_student_texts,
        hint_streak=hint_streak,
    )
    started = time.time()
    turn = socratic.process_turn(
        problem=session.problem,
        condition=session.condition,
        history=session.history,
        hint_level=session.hint_level,
        mastery=session.mastery,
        student_text=req.text,
        current_topic=session.topic,
        engagement_flag=engagement_flag,
        language=session.language,
    )
    latency_ms = int((time.time() - started) * 1000)

    # Persist conversation + bookkeeping.
    session.history.append({"role": "user", "content": req.text})
    session.history.append({"role": "assistant", "content": turn.tutor_message})
    session.hint_level = turn.hint_level
    session.mastery = turn.mastery
    session.is_solved = session.is_solved or turn.is_solved
    session.turns += 1
    session.last_activity_at = time.time()
    session.recent_student_texts.append(req.text)
    session.recent_student_texts = session.recent_student_texts[-5:]
    session.hint_request_streak = hint_streak

    store.log_turn(
        session, req.text, turn.model_dump(), latency_ms,
        response_time_ms=response_time_ms,
    )
    return turn


@app.get("/session/{session_id}", response_model=SessionState)
def get_session_state(session_id: str):
    session = store.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown session_id")
    return SessionState(
        session_id=session.session_id,
        problem=problems.to_public(session.problem) if session.problem else None,
        condition=session.condition,
        turns=session.turns,
        hint_level=session.hint_level,
        mastery=session.mastery,
        is_solved=session.is_solved,
    )


@app.get("/favorites", response_model=list[Favorite])
def get_favorites(student_id: str = Query(min_length=1)):
    normalized_id = student_id.strip()
    if not normalized_id or normalized_id == "anon":
        raise HTTPException(status_code=400, detail="A student name is required")
    return store.list_favorites(normalized_id)


@app.post("/favorites", response_model=Favorite)
def create_favorite(req: FavoriteCreate):
    student_id = req.student_id.strip()
    if not student_id or student_id == "anon":
        raise HTTPException(status_code=400, detail="A student name is required")
    if req.class_id not in {item["id"] for item in config.CLASS_OPTIONS}:
        raise HTTPException(status_code=400, detail="Unknown class_id")

    question = generator.get(req.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Unknown question_id")

    snapshot = {
        "question_id": question["id"],
        "student_id": student_id,
        "class_id": req.class_id,
        "topic": question["topic"],
        "stem": question["stem"],
        "type": question["type"],
        "difficulty": question["difficulty"],
        "instructions": question.get("instructions", ""),
        "options": question.get("options"),
        "steps": question.get("steps_shuffled"),
        "n_blanks": (
            len(question.get("blank_answers", []))
            if question["type"] == "fill_blank" else None
        ),
        "saved_at": time.time(),
    }
    return store.add_favorite(snapshot)


@app.delete("/favorites/{question_id}")
def delete_favorite(
    question_id: str,
    student_id: str = Query(min_length=1),
):
    normalized_id = student_id.strip()
    if not normalized_id or normalized_id == "anon":
        raise HTTPException(status_code=400, detail="A student name is required")
    if not store.remove_favorite(normalized_id, question_id):
        raise HTTPException(status_code=404, detail="Favorite not found")
    return {"removed": True}
