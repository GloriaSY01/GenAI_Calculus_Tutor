"""Quick smoke test for LLM JSON reliability and the Socratic agent."""
from backend import llm, problems, socratic

print("== JSON reliability ==")
for i in range(5):
    try:
        d = llm.chat_json([
            {"role": "system", "content": "Reply with ONLY a JSON object."},
            {"role": "user", "content": 'Return a JSON object with fields action="probe" and tutor_message="why?".'},
        ])
        print(i, "OK", d)
    except Exception as e:  # noqa: BLE001
        print(i, "FAIL", repr(e))

print("\n== Socratic agent ==")
p = problems.get_problem("der_003")
for txt in [
    "I will use the chain rule because it is a function raised to a power",
    "the derivative is 30x(3x^2+1)^4",
]:
    t = socratic.process_turn(p, "explain", [], 0, 0, txt)
    print(f"[{t.action}/{t.reasoning_assessment}] {t.tutor_message[:90]}")
