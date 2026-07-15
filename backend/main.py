"""FastAPI application exposing the Socratic tutor.

Endpoints:
  GET  /health                       -> liveness + model info
  GET  /problems                     -> public problem list (no answers)
  POST /session/start                -> create a session, get opening message
  POST /session/{sid}/message        -> send a student message, get tutor turn
  GET  /session/{sid}                -> current session state
"""
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import (
    analytics,
    assignments,
    config,
    generator,
    learning_path,
    problems,
    socratic,
    store,
)
from .schemas import (
    AnalyticsAnswer,
    AnalyticsQuery,
    Assignment,
    AssignmentCreate,
    ClassAnalytics,
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

TOPICS = ["Limits", "Derivatives", "Integrals", "Applications of Derivatives",
          "Continuity", "Chain Rule", "Related Rates"]

app = FastAPI(title="GenAI Calculus Tutor", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "model": config.LLM_MODEL, "base_url": config.LLM_BASE_URL}


@app.get("/problems", response_model=list[ProblemPublic])
def get_problems():
    return problems.list_problems()


@app.get("/topics", response_model=list[str])
def get_topics():
    return TOPICS


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
    answer = analytics.answer_question(req.question, data)
    return AnalyticsAnswer(answer=answer, grounded_on=data)


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
        return generator.generate_question(req.type, req.topic, req.difficulty)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502,
                            detail=f"Generation failed: {exc}") from exc


@app.post("/grade", response_model=GradeResponse)
def grade(req: GradeRequest):
    try:
        return generator.grade(req)
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

    session = store.create_session(problem, req.condition, req.student_id or "anon")
    opening = socratic.opening_message(problem, req.condition)
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

    started = time.time()
    turn = socratic.process_turn(
        problem=session.problem,
        condition=session.condition,
        history=session.history,
        hint_level=session.hint_level,
        mastery=session.mastery,
        student_text=req.text,
    )
    latency_ms = int((time.time() - started) * 1000)

    # Persist conversation + bookkeeping.
    session.history.append({"role": "user", "content": req.text})
    session.history.append({"role": "assistant", "content": turn.tutor_message})
    session.hint_level = turn.hint_level
    session.mastery = turn.mastery
    session.is_solved = session.is_solved or turn.is_solved
    session.turns += 1

    store.log_turn(session, req.text, turn.model_dump(), latency_ms)
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
