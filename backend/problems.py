"""Loads the Calculus 1 problem bank from disk."""
import json
from functools import lru_cache
from typing import Dict, List

from . import config
from .schemas import Problem, ProblemPublic


@lru_cache(maxsize=1)
def _load() -> Dict[str, Problem]:
    with open(config.PROBLEMS_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {item["id"]: Problem(**item) for item in raw}


def list_problems() -> List[ProblemPublic]:
    return [ProblemPublic(**p.model_dump()) for p in _load().values()]


def get_problem(problem_id: str) -> Problem | None:
    return _load().get(problem_id)


def to_public(problem: Problem) -> ProblemPublic:
    return ProblemPublic(**problem.model_dump())
