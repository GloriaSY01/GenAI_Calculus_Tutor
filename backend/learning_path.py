"""Loads the recommended Calculus 1 learning order.

Beginners often don't know *which* topic to start with or in what order.
This module exposes a curated, prerequisite-aware sequence so the student UI
can guide a first-time learner instead of dropping them onto a blank topic
picker.
"""
import json
from functools import lru_cache
from typing import List

from . import config
from .schemas import LearningStep


@lru_cache(maxsize=1)
def load_path() -> List[LearningStep]:
    with open(config.LEARNING_PATH_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    steps = [LearningStep(**item) for item in raw]
    return sorted(steps, key=lambda s: s.order)
