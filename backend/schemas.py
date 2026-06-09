"""Pydantic models for API requests/responses and internal state."""
from typing import List, Literal, Optional

from pydantic import BaseModel

Condition = Literal["explain", "control"]
QuestionType = Literal["single_choice", "multiple_choice", "fill_blank", "drag_order"]


class Problem(BaseModel):
    id: str
    topic: str
    difficulty: str
    tags: List[str]
    statement: str
    # The fields below are reference material for the tutor only; they are
    # never sent to the student client.
    final_answer: str
    key_idea: str
    solution_steps: List[str]


class ProblemPublic(BaseModel):
    """Problem view exposed to the frontend (no answers)."""
    id: str
    topic: str
    difficulty: str
    tags: List[str]
    statement: str


class StartSessionRequest(BaseModel):
    problem_id: Optional[str] = None  # None => free chat (no fixed problem)
    condition: Condition = "explain"
    student_id: Optional[str] = None


class MessageRequest(BaseModel):
    text: str


class TutorTurn(BaseModel):
    """Structured result of one tutor response."""
    tutor_message: str
    reasoning_assessment: Literal["none", "weak", "partial", "adequate", "strong"]
    action: Literal["probe", "hint", "correct", "affirm", "advance", "complete", "blocked"]
    asks_for_explanation: bool
    hint_level: int
    mastery: int
    is_solved: bool


class SessionState(BaseModel):
    session_id: str
    problem: Optional[ProblemPublic] = None
    condition: Condition
    turns: int
    hint_level: int
    mastery: int
    is_solved: bool


class StartSessionResponse(BaseModel):
    session_id: str
    problem: Optional[ProblemPublic] = None
    condition: Condition
    opening_message: str


# --------------------------------------------------------------------------- #
# Content generation (2.1)
# --------------------------------------------------------------------------- #
class GenerateRequest(BaseModel):
    type: QuestionType
    topic: str
    difficulty: str = "medium"


class GeneratedQuestionPublic(BaseModel):
    """Question view sent to the client (answers withheld)."""
    id: str
    type: QuestionType
    topic: str
    difficulty: str
    stem: str
    options: Optional[List[str]] = None      # single/multiple choice
    steps: Optional[List[str]] = None        # drag_order: shuffled steps
    n_blanks: Optional[int] = None           # fill_blank
    instructions: str = ""


class GradeRequest(BaseModel):
    question_id: str
    single: Optional[int] = None             # single_choice: chosen index
    multiple: Optional[List[int]] = None     # multiple_choice: chosen indices
    blanks: Optional[List[str]] = None       # fill_blank: text per blank
    order: Optional[List[str]] = None        # drag_order: steps in chosen order


class GradeResponse(BaseModel):
    correct: bool
    feedback: str
    correct_answer: str
