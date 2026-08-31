"""Plain-language findings (diagnosis only — actions live in the Act section).

The cards are built CLIENT-SIDE from the analytics payload (same thresholds as
`backend/analytics.build_insights`), because the backend renders its insight
text in English only. Building them here makes findings bilingual. Once the
backend ships structured insights (design doc §5 · B7), this module can consume
those instead.

Data: the full `GET /analytics/class` payload.
"""
from __future__ import annotations

import html

import streamlit as st

import ui
from i18n import t, topic_label
from teacher.topic_health import UNTIED_TOPICS

SEVERITY_ICON = {"info": "🟢", "warning": "🟠", "critical": "🔴"}
SEVERITY_CLASS = {"info": "sev-info", "warning": "sev-warning", "critical": "sev-critical"}

# Mirrors backend/analytics.build_insights.
_MIN_ATTEMPTS = 3
_WEAK_SOLVE_RATE = 0.6
_GAMING_CRITICAL = 0.3
_LOW_REASONING = 1.5
_HIGH_REASONING = 3.0
_THIN_SESSIONS = 5


def _msg(key: str, **params) -> tuple[str, str]:
    return (t(f"insight.{key}.title").format(**params),
            t(f"insight.{key}.detail").format(**params))


def build_local_insights(data: dict) -> list[dict]:
    cards: list[dict] = []

    by_topic = [row for row in data.get("by_topic", [])
                if row["topic"] not in UNTIED_TOPICS]
    ranked = [row for row in by_topic if row["attempts"] >= _MIN_ATTEMPTS] or by_topic
    if ranked:
        weakest = min(ranked, key=lambda r: (r["solve_rate"], r["avg_reasoning"]))
        if weakest["solve_rate"] < _WEAK_SOLVE_RATE:
            title, detail = _msg("weak_topic",
                                 topic=topic_label(weakest["topic"]),
                                 n=weakest["attempts"],
                                 solve=round(weakest["solve_rate"] * 100),
                                 reasoning=weakest["avg_reasoning"])
            cards.append({"severity": "warning", "title": title, "detail": detail})

    gaming = data.get("gaming_rate", 0)
    if gaming >= _GAMING_CRITICAL:
        title, detail = _msg("gaming_high", rate=round(gaming * 100))
        cards.append({"severity": "critical", "title": title, "detail": detail})
    elif gaming > 0:
        title, detail = _msg("gaming_low", rate=round(gaming * 100))
        cards.append({"severity": "info", "title": title, "detail": detail})

    reasoning = data.get("avg_reasoning", 0)
    if data.get("n_turns", 0) > 0:
        if reasoning < _LOW_REASONING:
            title, detail = _msg("low_reasoning", score=reasoning)
            cards.append({"severity": "warning", "title": title, "detail": detail})
        elif reasoning >= _HIGH_REASONING:
            title, detail = _msg("high_reasoning", score=reasoning)
            cards.append({"severity": "info", "title": title, "detail": detail})

    if data.get("n_sessions", 0) < _THIN_SESSIONS:
        title, detail = _msg("coverage", n=data.get("n_sessions", 0))
        cards.append({"severity": "info", "title": title, "detail": detail})

    if not cards:
        title, detail = _msg("healthy")
        cards.append({"severity": "info", "title": title, "detail": detail})
    return cards


def _card_html(card: dict) -> str:
    icon = SEVERITY_ICON.get(card["severity"], "🟢")
    css = SEVERITY_CLASS.get(card["severity"], "sev-info")
    return (f'<div class="insight {css}">'
            f'<div class="insight-title">{icon} {html.escape(card["title"])}</div>'
            f'<div class="insight-detail">{html.escape(card["detail"])}</div></div>')


# Beyond this many cards the list scrolls in place instead of stretching the page.
_SCROLL_AFTER = 3
_SCROLL_HEIGHT = 380


def render_insights_panel(data: dict) -> None:
    with st.container(border=True):
        ui.panel_header("💡", t("teacher.insights"), t("teacher.insights_caption"))
        cards = build_local_insights(data)
        body = (st.container(height=_SCROLL_HEIGHT) if len(cards) > _SCROLL_AFTER
                else st.container())
        with body:
            for card in cards:
                st.markdown(_card_html(card), unsafe_allow_html=True)
