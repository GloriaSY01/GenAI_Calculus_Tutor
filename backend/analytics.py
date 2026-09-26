"""Class-level analytics over the tutoring logs (teacher-facing).

Design notes (following the review feedback):
- The teacher view is about the CLASS, not individuals. Everything here
  aggregates across sessions/students; we never surface a single student's
  identity in the returned stats.
- We don't just dump descriptive statistics: `build_insights` turns the numbers
  into a small set of actionable insight cards (weak topic, gaming signals,
  low engagement, thin coverage), which the UI shows as plain-language findings.
- "Gaming" (pretending to learn / gaming the tutor) is flagged with light
  heuristics: guardrail hits ("just give me the answer"), near-instant turns,
  and empty/near-empty explanations. This is intentionally simple and explained
  to the teacher rather than hidden.

Reads data/logs/*.jsonl, which store.py appends to per session.
"""
from __future__ import annotations

import json
import logging
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from . import config, textbook
from .schemas import AnalyticsInsight, ClassAnalytics, TopicStat

log = logging.getLogger(__name__)

ASSESSMENT_SCORE = {"none": 0, "weak": 1, "partial": 2, "adequate": 3, "strong": 4}
_ASSESSMENT_LEVELS = ["none", "weak", "partial", "adequate", "strong"]

# Heuristic thresholds for gaming / low-effort behaviour.
_FAST_TURN_MS = 1500          # replies faster than this look like rushing
_SHORT_EXPLANATION_WORDS = 2  # "idk", "yes", single tokens


def _student_account(value: str | None) -> str | None:
    student_id = (value or "").strip()
    if not student_id or student_id.lower() == "anon":
        return None
    return student_id


def _load_events() -> List[dict]:
    events: List[dict] = []
    if not config.LOG_DIR.exists():
        return events
    for path in sorted(config.LOG_DIR.glob("*.jsonl")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        events.append(json.loads(line))
        except (OSError, json.JSONDecodeError):
            continue
    return events


def _empty_analytics() -> ClassAnalytics:
    return ClassAnalytics(
        n_sessions=0, n_students=0, n_turns=0, solve_rate=0.0,
        avg_reasoning=0.0, avg_final_mastery=0.0, avg_turns_per_session=0.0,
        gaming_rate=0.0, guardrail_rate=0.0, by_topic=[],
        reasoning_distribution={lvl: 0.0 for lvl in _ASSESSMENT_LEVELS},
        insights=[AnalyticsInsight(
            kind="coverage", severity="info",
            params=dict(n_sessions=0),
            title="No class data yet",
            detail="No tutoring sessions have been logged. Once students use "
                   "the tutor, class insights will appear here.",
        )],
    )


def compute(class_id: str | None = None) -> ClassAnalytics:
    events = _load_events()
    if class_id:
        session_ids = {e.get("session_id") for e in events
                       if e.get("event") == "session_start" and e.get("class_id") == class_id}
        events = [e for e in events if e.get("class_id") == class_id
                  or (e.get("session_id") is not None and e.get("session_id") in session_ids)]
    # Canonicalise before aggregation so section IDs and titles share one row.
    aliases = {}
    for _, section in textbook.iter_sections():
        info = textbook.get_section(section["id"])
        if info:
            for name in (info["id"], info["title"], info["display_title"]):
                aliases[name] = info["display_title"]
    events = [{**e, "topic": aliases.get(e.get("section_id") or e.get("topic"), e.get("topic"))} for e in events]
    result = _compute_events(events)
    practice = _compute_practice(events)
    result.practice = practice
    result.practice_submission_count = practice["n_answers"]
    result.independent_solve_rate = practice["independent_solve_rate"]
    result.ai_assisted_solve_rate = practice["ai_assisted_solve_rate"]

    practice_students = {
        student_id
        for e in events
        if e.get("event") == "practice_grade"
        for student_id in [_student_account(e.get("student_id"))]
        if student_id is not None
    }
    if practice_students:
        result.n_students = max(result.n_students, len(practice_students))
    return result


def _compute_practice(events: List[dict]) -> dict:
    rows = [e for e in events if e.get("event") == "practice_grade"]
    assisted_keys = {
        (e.get("class_id"), (e.get("student_id") or "anon").strip() or "anon", e.get("problem_id"))
        for e in events
        if e.get("event") == "session_start" and e.get("problem_id") not in (None, "free")
    }

    by_topic: Dict[str, dict] = defaultdict(
        lambda: {
            "attempts": 0,
            "correct": 0,
            "independent_count": 0,
            "ai_assisted_count": 0,
            "not_correct_count": 0,
        }
    )
    by_difficulty: Dict[str, dict] = defaultdict(
        lambda: {
            "attempts": 0,
            "independent_count": 0,
            "ai_assisted_count": 0,
            "not_correct_count": 0,
        }
    )

    for e in rows:
        student_id = _student_account(e.get("student_id")) or "anon"
        key = (e.get("class_id"), student_id, e.get("question_id"))
        assisted = (
            bool(e.get("ai_assisted"))
            or e.get("hint_usage") == "ai_assisted"
            or key in assisted_keys
        )
        correct = bool(e.get("correct"))
        topic = e.get("topic") or "General / Free chat"
        difficulty = e.get("difficulty") or "unknown"

        for bucket in (by_topic[topic], by_difficulty[difficulty]):
            bucket["attempts"] += 1
            if assisted:
                bucket["ai_help_count"] = bucket.get("ai_help_count", 0) + 1
            if correct:
                bucket["correct"] = bucket.get("correct", 0) + 1
                if assisted:
                    bucket["ai_assisted_count"] += 1
                else:
                    bucket["independent_count"] += 1
            else:
                bucket["not_correct_count"] += 1

    def enrich(bucket: dict) -> dict:
        attempts = bucket["attempts"]
        independent_count = bucket["independent_count"]
        ai_assisted_count = bucket["ai_assisted_count"]
        not_correct_count = bucket["not_correct_count"]
        ai_help_count = bucket.get("ai_help_count", 0)
        correct_count = independent_count + ai_assisted_count
        return {
            **bucket,
            "correct_rate": round(correct_count / attempts, 3) if attempts else 0.0,
            "ai_help_rate": round(ai_help_count / attempts, 3) if attempts else 0.0,
            "independent_rate": round(independent_count / attempts, 3) if attempts else 0.0,
            "ai_assisted_rate": round(ai_assisted_count / attempts, 3) if attempts else 0.0,
            "not_correct_rate": round(not_correct_count / attempts, 3) if attempts else 0.0,
        }

    topic_rows = [
        {"topic": topic, **enrich(bucket)}
        for topic, bucket in sorted(by_topic.items())
    ]
    difficulty_rows = [
        {"difficulty": difficulty, **enrich(bucket)}
        for difficulty, bucket in sorted(by_difficulty.items())
    ]

    n_answers = len(rows)
    independent_correct = sum(row["independent_count"] for row in topic_rows)
    ai_assisted_correct = sum(row["ai_assisted_count"] for row in topic_rows)
    ai_help_count = sum(row.get("ai_help_count", 0) for row in topic_rows)
    not_correct = sum(row["not_correct_count"] for row in topic_rows)
    correct_total = independent_correct + ai_assisted_correct

    return {
        "n_answers": n_answers,
        "correct_rate": round(correct_total / n_answers, 3) if n_answers else 0.0,
        "ai_help_count": ai_help_count,
        "ai_help_rate": round(ai_help_count / n_answers, 3) if n_answers else 0.0,
        "independent_solve_rate": round(independent_correct / n_answers, 3) if n_answers else 0.0,
        "ai_assisted_solve_rate": round(ai_assisted_correct / n_answers, 3) if n_answers else 0.0,
        "practice_completion_modes": [
            {"mode": "independent", "count": independent_correct},
            {"mode": "ai_assisted", "count": ai_assisted_correct},
            {"mode": "not_correct", "count": not_correct},
        ],
        "by_difficulty_completion": difficulty_rows,
        "practice_by_topic": topic_rows,
    }


def _compute_events(events) -> ClassAnalytics:
    if not events:
        return _empty_analytics()

    # Session metadata + topic mapping.
    meta: Dict[str, dict] = {}
    for e in events:
        if e.get("event") == "session_start":
            meta[e["session_id"]] = {
                "student_id": e.get("student_id", "anon"),
                "problem_id": e.get("problem_id", "free"),
                # Optional explicit topic (used by simulated/demo logs; real
                # sessions omit it and fall back to the problem->topic map).
                "topic": e.get("topic"),
            }

    # Map problem_id -> topic via the seed bank (best effort).
    topic_of = _problem_topic_map()

    turns_by_session: Dict[str, list] = defaultdict(list)
    for e in events:
        if e.get("event") == "turn":
            turns_by_session[e["session_id"]].append(e)

    students = set()
    total_turns = 0
    guardrail_hits = 0
    per_session_rows = []
    topic_bucket: Dict[str, dict] = defaultdict(
        lambda: {"attempts": 0, "reasoning": [], "solved": [],
                 "mastery": [], "gaming_sessions": 0}
    )
    dist_counts = {lvl: 0 for lvl in _ASSESSMENT_LEVELS}

    for sid, turns in turns_by_session.items():
        info = meta.get(sid, {})
        student_account = _student_account(info.get("student_id"))
        if student_account:
            students.add(student_account)
        pid = info.get("problem_id", "free")
        topic = info.get("topic") or topic_of.get(pid, "General / Free chat")

        reasoning_scores = []
        mastery_vals = []
        solved = False
        fast_turns = 0
        short_expl = 0
        session_guardrail = 0

        for t in turns:
            total_turns += 1
            assessment = t.get("reasoning_assessment", "none")
            dist_counts[assessment] = dist_counts.get(assessment, 0) + 1
            reasoning_scores.append(ASSESSMENT_SCORE.get(assessment, 0))
            mastery_vals.append(t.get("mastery", 0))
            solved = solved or bool(t.get("is_solved", False))
            if t.get("action") == "blocked":
                guardrail_hits += 1
                session_guardrail += 1
            if t.get("latency_ms", 99999) < _FAST_TURN_MS:
                fast_turns += 1
            words = len((t.get("student_text", "") or "").split())
            if words <= _SHORT_EXPLANATION_WORDS:
                short_expl += 1

        n = len(turns)
        avg_reasoning = sum(reasoning_scores) / n if n else 0
        final_mastery = max(mastery_vals) if mastery_vals else 0
        # Gaming signal: guardrail hit, or a session dominated by rushed /
        # empty replies.
        is_gaming = (
            session_guardrail > 0
            or (n >= 2 and (fast_turns + short_expl) / n >= 0.6)
        )

        per_session_rows.append({
            "n_turns": n, "avg_reasoning": avg_reasoning,
            "final_mastery": final_mastery, "solved": solved,
            "is_gaming": is_gaming,
        })

        b = topic_bucket[topic]
        b["attempts"] += 1
        b["reasoning"].append(avg_reasoning)
        b["solved"].append(1 if solved else 0)
        b["mastery"].append(final_mastery)
        if is_gaming:
            b["gaming_sessions"] += 1

    n_sessions = len(per_session_rows)
    solve_rate = _mean([r["solved"] for r in per_session_rows])
    avg_reasoning = _mean([r["avg_reasoning"] for r in per_session_rows])
    avg_final_mastery = _mean([r["final_mastery"] for r in per_session_rows])
    avg_turns = _mean([r["n_turns"] for r in per_session_rows])
    gaming_rate = _mean([1 if r["is_gaming"] else 0 for r in per_session_rows])
    guardrail_rate = guardrail_hits / total_turns if total_turns else 0.0

    by_topic = []
    for topic, b in sorted(topic_bucket.items()):
        by_topic.append(TopicStat(
            topic=topic,
            attempts=b["attempts"],
            avg_reasoning=round(_mean(b["reasoning"]), 2),
            solve_rate=round(_mean(b["solved"]), 2),
            avg_final_mastery=round(_mean(b["mastery"]), 1),
            gaming_rate=round(b["gaming_sessions"] / b["attempts"], 2)
            if b["attempts"] else 0.0,
        ))

    total_dist = sum(dist_counts.values()) or 1
    reasoning_distribution = {
        lvl: round(dist_counts.get(lvl, 0) / total_dist, 3)
        for lvl in _ASSESSMENT_LEVELS
    }

    analytics = ClassAnalytics(
        n_sessions=n_sessions,
        n_students=len(students),
        n_turns=total_turns,
        solve_rate=round(solve_rate, 3),
        avg_reasoning=round(avg_reasoning, 2),
        avg_final_mastery=round(avg_final_mastery, 1),
        avg_turns_per_session=round(avg_turns, 1),
        gaming_rate=round(gaming_rate, 3),
        guardrail_rate=round(guardrail_rate, 3),
        by_topic=by_topic,
        reasoning_distribution=reasoning_distribution,
        insights=[],
    )
    analytics.insights = build_insights(analytics)
    return analytics


def build_insights(a: ClassAnalytics) -> List[AnalyticsInsight]:
    """Turn the aggregate numbers into a few plain-language findings."""
    insights: List[AnalyticsInsight] = []

    # Weakest topic (lowest solve rate with enough attempts). Require a few
    # sessions so a single-attempt topic can't dominate the "weakest" call.
    ranked = [t for t in a.by_topic if t.attempts >= 3]
    if not ranked:
        ranked = [t for t in a.by_topic if t.attempts >= 1]
    if ranked:
        weakest = min(ranked, key=lambda t: (t.solve_rate, t.avg_reasoning))
        if weakest.solve_rate < 0.6:
            insights.append(AnalyticsInsight(
                kind="weak_topic", severity="warning",
                params=dict(topic=weakest.topic, solve_rate=weakest.solve_rate, avg_reasoning=weakest.avg_reasoning, attempts=weakest.attempts),
                title=f"Class struggles most with {weakest.topic}",
                detail=f"Solve rate {int(weakest.solve_rate * 100)}% and average "
                       f"reasoning {weakest.avg_reasoning}/4 across "
                       f"{weakest.attempts} session(s). Consider a short review "
                       f"or assigning easier practice on this topic.",
            ))

    # Gaming behaviour.
    if a.gaming_rate >= 0.3:
        insights.append(AnalyticsInsight(
            kind="gaming", severity="critical",
            params=dict(gaming_rate=a.gaming_rate),
            title="Possible gaming / low-effort behaviour",
            detail=f"About {int(a.gaming_rate * 100)}% of sessions show rushing, "
                   f"empty explanations, or 'just give me the answer' attempts. "
                   f"These students may be gaming the tutor rather than reasoning.",
        ))
    elif a.gaming_rate > 0:
        insights.append(AnalyticsInsight(
            kind="gaming", severity="info",
            params=dict(gaming_rate=a.gaming_rate),
            title="Some low-effort turns detected",
            detail=f"{int(a.gaming_rate * 100)}% of sessions had rushed or empty "
                   f"replies. Worth watching but not widespread.",
        ))

    # Engagement / reasoning quality.
    if a.avg_reasoning < 1.5 and a.n_turns > 0:
        insights.append(AnalyticsInsight(
            kind="engagement", severity="warning",
            params=dict(avg_reasoning=a.avg_reasoning),
            title="Reasoning quality is low overall",
            detail=f"Average reasoning is {a.avg_reasoning}/4. Students are "
                   f"often stating steps without justifying them. Encourage "
                   f"'why/how' explanations.",
        ))
    elif a.avg_reasoning >= 3.0 and a.n_turns > 0:
        insights.append(AnalyticsInsight(
            kind="positive", severity="info",
            params=dict(avg_reasoning=a.avg_reasoning),
            title="Strong reasoning across the class",
            detail=f"Average reasoning is {a.avg_reasoning}/4 — students are "
                   f"explaining their thinking well.",
        ))

    # Coverage.
    if a.n_sessions < 5:
        insights.append(AnalyticsInsight(
            kind="coverage", severity="info",
            params=dict(n_sessions=a.n_sessions),
            title="Limited data so far",
            detail=f"Only {a.n_sessions} session(s) logged. Trends will become "
                   f"more reliable as more students practise.",
        ))

    if not insights:
        insights.append(AnalyticsInsight(
            kind="positive", severity="info",
            title="Class looks healthy",
            detail="No major weak spots or gaming signals stand out in the "
                   "current data.",
        ))
    return insights


def answer_question(
    question: str,
    a: ClassAnalytics,
    language: str = "en",
    history: Optional[List[dict]] = None,
) -> Tuple[str, bool]:
    """LLM-backed Q&A grounded on the aggregate stats.

    Returns (answer, llm_available). When the model can't be reached we still
    answer with a rule-based summary, but we say so via the flag instead of
    passing a canned line off as a real answer -- teachers were seeing the same
    reply to every question with no hint that the model was down.
    """
    facts = _facts_block(a)
    chat_context = _chat_context(history or [])
    try:
        from . import llm
        prompt = (
            "You are a teaching assistant helping a Calculus 1 instructor "
            "interpret CLASS-LEVEL analytics and plan teaching actions. The "
            "teacher may ask follow-up questions conversationally. Use ONLY "
            "the facts provided when mentioning class data; do not invent "
            "numbers. If the teacher asks for general teaching advice, make it "
            "practical and label it as a suggestion rather than a measured "
            "finding. Answer in 2-5 short sentences.\n\n"
            f"CLASS FACTS:\n{facts}\n\n"
            f"RECENT CHAT:\n{chat_context}\n\n"
            f"TEACHER QUESTION: {question}\n\nAnswer:"
        )
        answer = llm.chat(
            [{"role": "system", "content": "You are concise and data-grounded. " + ("Reply in Simplified Chinese." if language == "zh" else "Reply in English.")},
             {"role": "user", "content": prompt}],
            temperature=0.3, max_tokens=250, retries=1,
        ).strip()
        if answer:
            return answer, True
        log.warning("Analytics assistant: model returned an empty answer.")
    except Exception as exc:  # noqa: BLE001
        log.warning("Analytics assistant falling back to rules: %s", exc)
    return _fallback_answer(a, language), False


def _chat_context(history: List[dict], limit: int = 6) -> str:
    rows = []
    for msg in history[-limit:]:
        role = msg.get("role")
        content = (msg.get("content") or "").strip()
        if role in {"user", "assistant"} and content:
            speaker = "Teacher" if role == "user" else "Assistant"
            rows.append(f"{speaker}: {content[:800]}")
    return "\n".join(rows) if rows else "(no previous messages)"


def _facts_block(a: ClassAnalytics) -> str:
    lines = [
        f"- sessions: {a.n_sessions}, students: {a.n_students}, turns: {a.n_turns}",
        f"- solve_rate: {a.solve_rate}, avg_reasoning(0-4): {a.avg_reasoning}, "
        f"avg_final_mastery(0-100): {a.avg_final_mastery}",
        f"- avg_turns_per_session: {a.avg_turns_per_session}, "
        f"gaming_rate: {a.gaming_rate}, guardrail_rate: {a.guardrail_rate}",
        "- by topic (topic | attempts | solve_rate | avg_reasoning | gaming_rate):",
    ]
    for t in a.by_topic:
        lines.append(f"    {t.topic} | {t.attempts} | {t.solve_rate} | "
                     f"{t.avg_reasoning} | {t.gaming_rate}")
    return "\n".join(lines)


def _fallback_answer(a: ClassAnalytics, language: str = "en") -> str:
    if language == "zh":
        if not a.by_topic:
            return "暂无足够的班级数据，请在学生完成练习后再查看。"
        return (f"班级数据摘要：整体正确率 {int(a.solve_rate * 100)}%，"
                f"平均推理得分 {a.avg_reasoning}/4。可在知识点诊断页查看各知识点表现。")
    if not a.by_topic:
        return ("There isn't enough class data yet to answer. Once students use "
                "the tutor, ask again.")
    weakest = min(a.by_topic, key=lambda t: t.solve_rate)
    return (f"Based on the class data, the weakest area is {weakest.topic} "
            f"(solve rate {int(weakest.solve_rate * 100)}%). Overall solve rate "
            f"is {int(a.solve_rate * 100)}% and average reasoning is "
            f"{a.avg_reasoning}/4. Consider reviewing {weakest.topic} next.")


# --------------------------------------------------------------------------- #
def _mean(xs) -> float:
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def _problem_topic_map() -> Dict[str, str]:
    try:
        from . import problems
        return {p.id: p.topic for p in _seed_problems(problems)}
    except Exception:  # noqa: BLE001
        return {}


def _seed_problems(problems_module):
    # problems.list_problems() returns public views with topic attached.
    return problems_module.list_problems()
