"""End-to-end API conversation test against a running backend."""
import requests

B = "http://127.0.0.1:8000"

s = requests.post(B + "/session/start",
                  json={"problem_id": "lim_002", "condition": "explain",
                        "student_id": "apitest"}).json()
sid = s["session_id"]
print("OPENING:", s["opening_message"][:100], "\n")

turns = [
    "Direct substitution gives 0/0, so I need another method.",
    "I can factor the numerator since x^2-9 is a difference of squares: (x-3)(x+3).",
    "I cancel (x-3), leaving x+3, then substitute x=3 to get 6.",
]
for t in turns:
    r = requests.post(f"{B}/session/{sid}/message", json={"text": t}).json()
    print(f">> {t}")
    print(f"   [{r['action']}/{r['reasoning_assessment']}] solved={r['is_solved']} "
          f"mastery={r['mastery']}")
    print(f"   {r['tutor_message'][:120]}\n")

state = requests.get(f"{B}/session/{sid}").json()
print("FINAL STATE:", state)
