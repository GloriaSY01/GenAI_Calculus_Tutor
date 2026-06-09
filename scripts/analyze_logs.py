"""Analyze tutoring session logs for the explanation-driven learning study.

Reads every data/logs/*.jsonl file, builds per-turn and per-session tables, and
compares the two experimental conditions (explain vs control) on the metrics
that matter for the study:

  - reasoning quality   (assessment mapped to 0-4)
  - explanation length  (words the student wrote)
  - turns per session
  - solve rate
  - final mastery
  - guardrail trigger rate

Outputs:
  reports/turns.csv, reports/sessions.csv, reports/condition_summary.csv
  reports/figures/*.png

Usage:
  python -m scripts.analyze_logs
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless: write files, no GUI window
import matplotlib.pyplot as plt
import pandas as pd

from backend import config

REPORTS_DIR = config.ROOT_DIR / "reports"
FIG_DIR = REPORTS_DIR / "figures"

ASSESSMENT_SCORE = {"none": 0, "weak": 1, "partial": 2, "adequate": 3, "strong": 4}
CONDITION_ORDER = ["explain", "control"]
CONDITION_COLORS = {"explain": "#2a9d8f", "control": "#e76f51"}


def load_events() -> list[dict]:
    events = []
    for path in sorted(config.LOG_DIR.glob("*.jsonl")):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
    return events


def build_tables(events: list[dict]):
    # Session metadata from session_start events.
    meta = {
        e["session_id"]: {
            "condition": e.get("condition", "unknown"),
            "problem_id": e.get("problem_id", "?"),
            "student_id": e.get("student_id", "anon"),
        }
        for e in events
        if e.get("event") == "session_start"
    }

    rows = []
    for e in events:
        if e.get("event") != "turn":
            continue
        sid = e["session_id"]
        info = meta.get(sid, {})
        text = e.get("student_text", "") or ""
        rows.append({
            "session_id": sid,
            "condition": info.get("condition", "unknown"),
            "problem_id": info.get("problem_id", "?"),
            "student_id": info.get("student_id", "anon"),
            "turn_index": e.get("turn_index"),
            "assessment": e.get("reasoning_assessment", "none"),
            "reasoning_score": ASSESSMENT_SCORE.get(e.get("reasoning_assessment", "none"), 0),
            "action": e.get("action"),
            "asks_explanation": bool(e.get("asks_for_explanation", False)),
            "is_solved": bool(e.get("is_solved", False)),
            "mastery": e.get("mastery", 0),
            "hint_level": e.get("hint_level", 0),
            "latency_ms": e.get("latency_ms", 0),
            "explanation_words": len(text.split()),
            "is_guardrail": e.get("action") == "blocked",
        })
    turns = pd.DataFrame(rows)

    if turns.empty:
        return turns, pd.DataFrame()

    sessions = turns.groupby("session_id").agg(
        condition=("condition", "first"),
        problem_id=("problem_id", "first"),
        student_id=("student_id", "first"),
        n_turns=("turn_index", "count"),
        avg_reasoning=("reasoning_score", "mean"),
        avg_explanation_words=("explanation_words", "mean"),
        final_mastery=("mastery", "max"),
        solved=("is_solved", "any"),
        guardrail_hits=("is_guardrail", "sum"),
    ).reset_index()

    return turns, sessions


def condition_summary(sessions: pd.DataFrame) -> pd.DataFrame:
    g = sessions.groupby("condition")
    summary = pd.DataFrame({
        "n_sessions": g.size(),
        "avg_turns": g["n_turns"].mean(),
        "avg_reasoning_score": g["avg_reasoning"].mean(),
        "avg_explanation_words": g["avg_explanation_words"].mean(),
        "avg_final_mastery": g["final_mastery"].mean(),
        "solve_rate": g["solved"].mean(),
        "avg_guardrail_hits": g["guardrail_hits"].mean(),
    })
    return summary.reindex([c for c in CONDITION_ORDER if c in summary.index])


def _bar(ax, summary, col, title, ylabel):
    conds = list(summary.index)
    vals = summary[col].values
    colors = [CONDITION_COLORS.get(c, "#888") for c in conds]
    ax.bar(conds, vals, color=colors)
    ax.set_title(title, fontsize=11)
    ax.set_ylabel(ylabel)
    for i, v in enumerate(vals):
        ax.text(i, v, f"{v:.2f}", ha="center", va="bottom", fontsize=9)


def make_figures(turns: pd.DataFrame, summary: pd.DataFrame):
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    # 1) Condition comparison dashboard.
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    _bar(axes[0, 0], summary, "avg_reasoning_score",
         "Avg reasoning quality (0-4)", "score")
    _bar(axes[0, 1], summary, "avg_explanation_words",
         "Avg explanation length", "words")
    _bar(axes[1, 0], summary, "solve_rate", "Solve rate", "rate")
    _bar(axes[1, 1], summary, "avg_final_mastery", "Avg final mastery", "mastery")
    fig.suptitle("Explanation-driven learning: explain vs control",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(FIG_DIR / "condition_comparison.png", dpi=130)
    plt.close(fig)

    # 2) Reasoning-assessment distribution by condition.
    order = ["none", "weak", "partial", "adequate", "strong"]
    dist = (turns.groupby(["condition", "assessment"]).size()
            .unstack(fill_value=0).reindex(columns=order, fill_value=0))
    dist = dist.reindex([c for c in CONDITION_ORDER if c in dist.index])
    dist_pct = dist.div(dist.sum(axis=1), axis=0).fillna(0)

    fig2, ax2 = plt.subplots(figsize=(8, 4.5))
    bottom = pd.Series(0.0, index=dist_pct.index)
    cmap = plt.get_cmap("YlGn")
    for i, level in enumerate(order):
        ax2.bar(dist_pct.index, dist_pct[level], bottom=bottom,
                label=level, color=cmap(0.2 + 0.16 * i))
        bottom += dist_pct[level]
    ax2.set_title("Reasoning-assessment distribution by condition")
    ax2.set_ylabel("share of turns")
    ax2.legend(title="assessment", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig2.tight_layout()
    fig2.savefig(FIG_DIR / "assessment_distribution.png", dpi=130)
    plt.close(fig2)


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    events = load_events()
    turns, sessions = build_tables(events)

    if turns.empty:
        print("No turn data found in data/logs/. Run a few sessions first.")
        return

    summary = condition_summary(sessions)

    turns.to_csv(REPORTS_DIR / "turns.csv", index=False)
    sessions.to_csv(REPORTS_DIR / "sessions.csv", index=False)
    summary.to_csv(REPORTS_DIR / "condition_summary.csv")

    make_figures(turns, summary)

    pd.set_option("display.width", 120)
    pd.set_option("display.max_columns", 20)
    print(f"Loaded {len(events)} events | {len(sessions)} sessions | "
          f"{len(turns)} turns\n")
    print("=== Condition summary ===")
    print(summary.round(2).to_string())
    print(f"\nWrote CSVs to {REPORTS_DIR}")
    print(f"Wrote figures to {FIG_DIR}")


if __name__ == "__main__":
    main()
