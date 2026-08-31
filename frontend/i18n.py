"""Small bilingual copy helper for the Streamlit interface."""

from __future__ import annotations


def tr(language: str, english: str, chinese: str, **values) -> str:
    template = chinese if language == "zh" else english
    return template.format(**values)
