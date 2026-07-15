"""Generate simulated tutoring logs so the Teacher Dashboard charts are populated.

This writes realistic-looking JSONL session logs into data/logs/ using the same
schema store.py produces (session_start + turn events). Analytics then aggregates
them into class-level KPIs, per-topic bar charts, a reasoning distribution and
insight cards.

The simulated files are prefixed with "sim_" so they are easy to identify and
this script is idempotent (it removes previous sim_*.jsonl before regenerating).
Real sessions logged by the app are never touched.

Run:  python3 scripts/seed_demo_logs.py
"""
import json
import random
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT / "data" / "logs"

SEED = 42
random.seed(SEED)

LEVELS = ["none", "weak", "partial", "adequate", "strong"]

# Per-topic profile: (solve_rate_target, strength, gaming_prob, n_sessions).
# "strength" drives the reasoning-quality distribution; later/harder topics are
# weaker and show more gaming so the dashboard has meaningful contrast.
TOPIC_PROFILES = {
    "Limits":                     (0.82, "strong", 0.08, 7),
    "Continuity":                 (0.74, "strong", 0.10, 6),
    "Derivatives":                (0.66, "medium", 0.14, 8),
    "Chain Rule":                 (0.46, "weak",   0.28, 6),
    "Applications of Derivatives":(0.58, "medium", 0.18, 6),
    "Related Rates":              (0.34, "weak",   0.34, 5),
    "Integrals":                  (0.52, "medium", 0.22, 7),
}

STRENGTH_WEIGHTS = {
    "strong": [0.02, 0.08, 0.20, 0.40, 0.30],
    "medium": [0.05, 0.22, 0.35, 0.28, 0.10],
    "weak":   [0.16, 0.36, 0.30, 0.13, 0.05],
}

STUDENTS = [f"stu_{i:02d}" for i in range(1, 13)]  # 12 students in the "class"

GOOD_TEXTS = [
    "I think we substitute x = 0 first, but that gives 0/0 so we need to factor.",
    "Because the derivative measures the instantaneous rate of change here.",
    "We can multiply by the conjugate to remove the square root in the numerator.",
    "Using the chain rule, the outer derivative times the inner derivative.",
    "The limit exists because both one-sided limits agree at that point.",
    "I set the derivative to zero to find the critical points.",
]
SHORT_TEXTS = ["idk", "yes", "no", "answer?", "just tell me", ""]


def _sample_reasoning(strength: str) -> str:
    return random.choices(LEVELS, weights=STRENGTH_WEIGHTS[strength])[0]


def _write_session(fh_dir: Path, student: str, topic: str, solved: bool,
                   strength: str, gaming: bool, start_ts: float) -> None:
    sid = f"sim_{random.getrandbits(48):012x}"
    path = fh_dir / f"{sid}.jsonl"
    records = []
    ts = start_ts

    records.append({
        "ts": ts, "session_id": sid, "event": "session_start",
        "problem_id": f"{topic[:3].lower()}_demo", "topic": topic,
        "condition": random.choice(["explain", "control"]),
        "student_id": student,
    })

    n_turns = random.randint(3, 8)
    mastery = random.randint(8, 28)
    for i in range(n_turns):
        ts += random.uniform(8, 45)
        last = i == n_turns - 1

        if gaming:
            # Rushed / empty / "just give me the answer" behaviour.
            action = "blocked" if random.random() < 0.5 else "hint"
            latency = random.randint(300, 1400)
            student_text = random.choice(SHORT_TEXTS)
            assessment = random.choices(LEVELS, weights=[0.4, 0.4, 0.15, 0.05, 0])[0]
            mastery += random.randint(0, 4)
        else:
            action = "hint" if not last else ("solved" if solved else "hint")
            latency = random.randint(3000, 22000)
            student_text = random.choice(GOOD_TEXTS)
            assessment = _sample_reasoning(strength)
            mastery += random.randint(6, 16)

        mastery = min(mastery, 100)
        is_solved = bool(last and solved and not gaming)
        if is_solved:
            mastery = max(mastery, random.randint(72, 96))

        records.append({
            "ts": ts, "session_id": sid, "event": "turn",
            "turn_index": i, "student_text": student_text,
            "latency_ms": latency, "action": action,
            "reasoning_assessment": assessment,
            "mastery": mastery, "is_solved": is_solved,
        })

    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Idempotent: clear previously generated sim_*.jsonl only.
    removed = 0
    for p in LOG_DIR.glob("sim_*.jsonl"):
        p.unlink()
        removed += 1

    base_ts = time.time() - 6 * 24 * 3600  # spread across the last ~6 days
    total = 0
    for topic, (solve_target, strength, gaming_prob, n_sessions) in TOPIC_PROFILES.items():
        for _ in range(n_sessions):
            student = random.choice(STUDENTS)
            solved = random.random() < solve_target
            gaming = random.random() < gaming_prob
            start_ts = base_ts + random.uniform(0, 6 * 24 * 3600)
            _write_session(LOG_DIR, student, topic, solved, strength, gaming, start_ts)
            total += 1

    print(f"Removed {removed} old sim logs; wrote {total} simulated sessions "
          f"across {len(TOPIC_PROFILES)} topics into {LOG_DIR}")


if __name__ == "__main__":
    main()
