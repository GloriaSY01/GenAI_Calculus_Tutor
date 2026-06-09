"""Test content generation + grading for all four question types."""
from backend import generator
from backend.schemas import GradeRequest

CASES = [
    ("single_choice", "Derivatives", "easy"),
    ("multiple_choice", "Limits", "medium"),
    ("fill_blank", "Integrals", "easy"),
    ("drag_order", "Limits", "medium"),
]

for qtype, topic, diff in CASES:
    print(f"\n===== {qtype} / {topic} / {diff} =====")
    q = generator.generate_question(qtype, topic, diff)
    rec = generator.get(q.id)
    print("STEM:", q.stem)
    if q.options:
        for i, o in enumerate(q.options):
            print(f"   ({i}) {o}")
    if q.steps:
        print("   shuffled steps:", q.steps)
    if q.n_blanks:
        print("   blanks:", q.n_blanks)

    # Build the *correct* answer from the private record and grade it.
    if qtype == "single_choice":
        req = GradeRequest(question_id=q.id, single=rec["correct_indices"][0])
    elif qtype == "multiple_choice":
        req = GradeRequest(question_id=q.id, multiple=rec["correct_indices"])
    elif qtype == "fill_blank":
        req = GradeRequest(question_id=q.id, blanks=[a[0] for a in rec["blank_answers"]])
    else:
        req = GradeRequest(question_id=q.id, order=rec["steps_correct"])

    res = generator.grade(req)
    print("GRADE (should be correct):", res.correct)
    print("CORRECT ANSWER:", res.correct_answer)
