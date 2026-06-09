"""Seed a few demo sessions in both conditions so the analysis has data.

This drives the live API with scripted student turns of varying reasoning
quality. It is only for demoing the analytics pipeline; real study data would
come from actual students.

Usage (backend must be running):
  python -m scripts.seed_sessions
"""
import requests

B = "http://127.0.0.1:8000"

# (problem_id, [student turns]) with a mix of strong and weak reasoning.
SCRIPTS = [
    ("lim_002", [
        "Direct substitution gives 0/0, so it's indeterminate and I need to factor.",
        "x^2-9 factors as (x-3)(x+3) because it's a difference of squares.",
        "I cancel (x-3) since x is near 3 but not equal to 3, leaving x+3, which gives 6.",
    ]),
    ("der_003", [
        "It's a composite function, so I'll use the chain rule.",
        "Outer is (..)^5 and inner is 3x^2+1; derivative of outer is 5(..)^4.",
        "Inner derivative is 6x, so multiplying gives 30x(3x^2+1)^4.",
    ]),
    ("int_002", [
        "umm I think I just integrate normally",
        "maybe substitution?",
        "let u = x^2+1 because its derivative 2x is there, so it becomes u^3 du.",
    ]),
]

CONDITIONS = ["explain", "control"]


def run():
    for condition in CONDITIONS:
        for problem_id, turns in SCRIPTS:
            s = requests.post(B + "/session/start", json={
                "problem_id": problem_id, "condition": condition,
                "student_id": f"seed_{condition}",
            }).json()
            sid = s["session_id"]
            for t in turns:
                requests.post(f"{B}/session/{sid}/message", json={"text": t})
            print(f"seeded {condition:8s} {problem_id} -> {sid}")


if __name__ == "__main__":
    run()
