"""Pydantic models for API requests/responses and internal state."""
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

Condition = Literal["explain", "control"]
Language = Literal["en", "zh"]
QuestionType = Literal["single_choice", "multiple_choice", "fill_blank", "drag_order"]


class Problem(BaseModel):
    id: str
    topic: str
    section_id: Optional[str] = None
    difficulty: str
    tags: List[str]
    statement: str
    source: Literal["seed", "textbook", "generated"] = "seed"
    citations: List["Citation"] = Field(default_factory=list)
    # The fields below are reference material for the tutor only; they are
    # never sent to the student client.
    final_answer: str
    key_idea: str
    solution_steps: List[str]


class ProblemPublic(BaseModel):
    """Problem view exposed to the frontend (no answers)."""
    id: str
    topic: str
    section_id: Optional[str] = None
    difficulty: str
    tags: List[str]
    statement: str
    source: Literal["seed", "textbook", "generated"] = "seed"
    citations: List["Citation"] = Field(default_factory=list)


class StartSessionRequest(BaseModel):
    problem_id: Optional[str] = None  # None => free chat (no fixed problem)
    condition: Condition = "explain"
    student_id: Optional[str] = None
    class_id: Optional[str] = None
    topic: Optional[str] = None
    language: Language = "en"


class MessageRequest(BaseModel):
    text: str
    language: Optional[Language] = None


class Citation(BaseModel):
    number: int
    source: str
    title: str
    section: str
    url: str
    page: Optional[int] = None


class TutorTurn(BaseModel):
    """Structured result of one tutor response."""
    tutor_message: str
    reasoning_assessment: Literal["none", "weak", "partial", "adequate", "strong"]
    action: Literal["probe", "hint", "correct", "affirm", "advance", "complete", "blocked"]
    asks_for_explanation: bool
    hint_level: int
    mastery: int
    is_solved: bool
    citations: List[Citation] = Field(default_factory=list)
    engagement_flag: Optional[str] = None
    safety_event: Optional[str] = None


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


class TextbookFigure(BaseModel):
    id: str
    url: str
    figure_number: str = ""
    caption: str = ""
    printed_page: Optional[int] = None


class ConceptContentBlock(BaseModel):
    id: str
    content_type: Literal["concept", "example"]
    subtype: str
    heading: str
    text: str
    formulas: List[str] = Field(default_factory=list)
    order: int = 0
    printed_page: Optional[int] = None
    requires_figure: bool = False
    figures: List[TextbookFigure] = Field(default_factory=list)


class ConceptCard(BaseModel):
    topic: str
    title: str
    chapter: str = ""
    summary: str
    definition: str = ""
    formulas: List[str] = Field(default_factory=list)
    example: str = ""
    pitfalls: str = ""
    source_url: str = ""
    source: str = ""
    publisher: str = ""
    license: str = ""
    attribution: str = ""
    term: str = ""
    content: List[ConceptContentBlock] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)


class CatalogSection(BaseModel):
    id: str
    label: str = ""
    title: str
    url: str


class CatalogChapter(BaseModel):
    id: str
    title: str
    sections: List[CatalogSection]


class CatalogResponse(BaseModel):
    source: str
    attribution: str
    license: str
    url: str
    default_section_id: str
    chapters: List[CatalogChapter]


class ClassOption(BaseModel):
    id: str
    label: str


# --------------------------------------------------------------------------- #
# Content generation (2.1)
# --------------------------------------------------------------------------- #
class GenerateRequest(BaseModel):
    type: QuestionType
    topic: str
    difficulty: str = "medium"
    language: Language = "en"


class GeneratedQuestionPublic(BaseModel):
    """Question view sent to the client (answers withheld)."""
    id: str
    type: QuestionType
    topic: str
    section_id: Optional[str] = None
    difficulty: str
    stem: str
    options: Optional[List[str]] = None      # single/multiple choice
    steps: Optional[List[str]] = None        # drag_order: shuffled steps
    n_blanks: Optional[int] = None           # fill_blank
    instructions: str = ""
    source: Literal["textbook", "generated"] = "generated"
    citations: List[Citation] = Field(default_factory=list)


class GradeRequest(BaseModel):
    question_id: str
    student_id: Optional[str] = None
    class_id: Optional[str] = None
    single: Optional[int] = None             # single_choice: chosen index
    multiple: Optional[List[int]] = None     # multiple_choice: chosen indices
    blanks: Optional[List[str]] = None       # fill_blank: text per blank
    order: Optional[List[str]] = None        # drag_order: steps in chosen order


class GradeResponse(BaseModel):
    correct: bool
    feedback: str
    correct_answer: Optional[str] = None
    attempts: int = 1
    answer_revealed: bool = False


class FavoriteCreate(BaseModel):
    student_id: str = Field(min_length=1)
    class_id: str = Field(min_length=1)
    question_id: str = Field(min_length=1)


class Favorite(BaseModel):
    question_id: str
    student_id: str
    class_id: str
    topic: str
    stem: str
    type: QuestionType
    difficulty: str
    instructions: str = ""
    options: Optional[List[str]] = None
    steps: Optional[List[str]] = None
    n_blanks: Optional[int] = None
    saved_at: float


# --------------------------------------------------------------------------- #
# Learning path (student onboarding / guided order)
# --------------------------------------------------------------------------- #
class LearningStep(BaseModel):
    """One node in the recommended Calculus 1 learning order."""
    order: int
    topic: str
    title: str
    summary: str
    prerequisites: List[str] = []
    starter_type: QuestionType = "single_choice"
    starter_difficulty: str = "easy"


# --------------------------------------------------------------------------- #
# Teacher analytics (class-level, never per-identified-student by default)
# --------------------------------------------------------------------------- #
class TopicStat(BaseModel):
    topic: str
    attempts: int
    avg_reasoning: float          # 0-4 scale
    solve_rate: float             # 0-1
    avg_final_mastery: float      # 0-100
    gaming_rate: float            # 0-1 (share of sessions with gaming signals)


class AnalyticsInsight(BaseModel):
    kind: Literal["weak_topic", "gaming", "engagement", "coverage", "positive"]
    severity: Literal["info", "warning", "critical"]
    title: str
    detail: str


class ClassAnalytics(BaseModel):
    n_sessions: int
    n_students: int
    n_turns: int
    solve_rate: float
    avg_reasoning: float
    avg_final_mastery: float
    avg_turns_per_session: float
    gaming_rate: float
    guardrail_rate: float
    by_topic: List[TopicStat]
    reasoning_distribution: dict           # level -> share
    insights: List[AnalyticsInsight]


class AnalyticsQuery(BaseModel):
    question: str


class AnalyticsAnswer(BaseModel):
    answer: str
    grounded_on: ClassAnalytics
    # False => the model was unreachable and `answer` is a rule-based summary,
    # so the UI can say so rather than presenting it as a real reply.
    llm_available: bool = True


# --------------------------------------------------------------------------- #
# Assignments (teacher assigns practice to the class)
# --------------------------------------------------------------------------- #
class AssignmentItem(BaseModel):
    """One block of questions inside an assignment.

    An assignment is a LIST of these, so a single task can mix topics,
    question types and difficulties (e.g. 4 easy single-choice to warm up,
    then 3 medium fill-in-the-blank, then 2 hard ordering exercises).
    """
    topic: str
    qtype: QuestionType
    difficulty: str = "medium"
    count: int = 1


class AssignmentCreate(BaseModel):
    title: str
    note: str = ""
    items: List[AssignmentItem]


class Assignment(AssignmentCreate):
    id: str
    created_at: float
