"""Run deterministic safety checks and optional local RAG retrieval checks."""
from __future__ import annotations

import json
import time
from pathlib import Path

from backend import guardrail, rag, socratic

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "data" / "eval" / "agent_golden.json"

RETRIEVAL_CASES = [
    ("mit-2-6-limits", "What does it mean for the limit of a function to exist?", "Limits"),
    ("mit-4-1-the-chain-rule", "How do nested functions change differentiation?", "The Chain Rule"),
    ("mit-5-5-the-definite-integral", "How is a definite integral related to sums?", "The Definite Integral"),
]

STRUCTURED_REPLIES = [
    (
        "ASSESSMENT: weak\nACTION: probe\nASKS_EXPLANATION: yes\nSOLVED: no\n"
        "MASTERY_GAIN: no\nMESSAGE: Why does that rule apply?",
        "probe",
    ),
    (
        "ASSESSMENT: adequate\nACTION: advance\nASKS_EXPLANATION: no\nSOLVED: no\n"
        "MASTERY_GAIN: yes\nMESSAGE: Good reasoning. What is the next small step?",
        "advance",
    ),
]


def main() -> None:
    cases = json.loads(GOLDEN.read_text(encoding="utf-8"))
    correct = sum(
        guardrail.check_input(case["text"]) == case["expected_input_guard"]
        for case in cases
    )
    false_positives = sum(
        guardrail.check_input(case["text"]) is not None
        and case["expected_input_guard"] is None
        for case in cases
    )
    print(f"input_guard_accuracy: {correct / len(cases):.3f} ({correct}/{len(cases)})")
    print(f"normal_request_false_positive_rate: {false_positives / len(cases):.3f}")

    parsed = 0
    compliant = 0
    for reply, expected_action in STRUCTURED_REPLIES:
        fields, message = socratic._parse_response(reply)
        parsed += bool(fields and message)
        compliant += fields.get("ACTION", "").lower() == expected_action
    structured_total = len(STRUCTURED_REPLIES)
    print(f"structured_parse_success: {parsed / structured_total:.3f}")
    print(f"action_policy_fixture_compliance: {compliant / structured_total:.3f}")

    leak_cases = [
        ("The final answer is 2x.", "2x", True),
        ("Which differentiation rule would you apply first?", "2x", False),
    ]
    leak_correct = sum(
        bool(guardrail.check_output(text, answer)) == expected
        for text, answer, expected in leak_cases
    )
    print(f"answer_leak_detection_accuracy: {leak_correct / len(leak_cases):.3f}")

    try:
        cold_started = time.perf_counter()
        rag.retrieve(RETRIEVAL_CASES[0][1], section_id=RETRIEVAL_CASES[0][0], k=3)
        cold_start_ms = (time.perf_counter() - cold_started) * 1000
        retrieval_started = time.perf_counter()
        hits = 0
        citations_present = 0
        for section_id, query, expected_title in RETRIEVAL_CASES:
            results = rag.retrieve(query, section_id=section_id, k=3)
            hits += any(expected_title in item.get("title", "") for item in results)
            citations_present += bool(
                results and all(item.get("source_url") for item in results)
            )
        total = len(RETRIEVAL_CASES)
        print(f"retrieval_hit_at_3: {hits / total:.3f} ({hits}/{total})")
        print(f"citation_coverage: {citations_present / total:.3f}")
        print(f"cold_start_retrieval_latency_ms: {cold_start_ms:.1f}")
        print(
            "mean_warm_retrieval_latency_ms: "
            f"{(time.perf_counter() - retrieval_started) * 1000 / total:.1f}"
        )
    except rag.RAGUnavailable as exc:
        print(f"retrieval_metrics: skipped ({exc})")


if __name__ == "__main__":
    main()
