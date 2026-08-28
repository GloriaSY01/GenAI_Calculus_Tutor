# GenAI Calculus Tutor

*English | [中文](README.zh-CN.md)*

A prototype GenAI system for **Calculus 1**. The page shows two blocks
**side by side** (left and right):

- **Block A (left) — Practice (content generation, 2.1):** an LLM generates
  calculus questions in four formats — **single choice, multiple choice,
  fill-in-the-blank, and drag-to-order (process) exercises** — which the student
  answers and gets auto-graded.
- **Block B (right) — Tutor (AI agent, 2.2):** a **Socratic AI tutor** that
  never hands over the answer, asks the student to **explain their reasoning**,
  and guides them step by step. It works as **free chat by default** (ask
  anything), and can optionally be **linked** to the current left-side question.

The two blocks are independent: the tutor is usable on its own, and linking is
a one-click action.

Built with **FastAPI** (backend) + **Streamlit** (frontend). This is the demo for
the capstone project on *explanation-driven learning in college mathematics*,
designed to be extended into a Learnvia-compatible module later.

---

## Why this design

The project background emphasizes capturing students' **explanations,
justifications, and revisions**. To make that the centerpiece (and to give the
planned study a clean comparison), the tutor supports two **experimental
conditions**:

| Condition | Behavior | Role |
|---|---|---|
| `explain` | **Explain-to-unlock**: the student must justify their reasoning ("why/how") before the tutor advances to the next hint. | Treatment group |
| `control` | Normal progressive Socratic hints, no forced explanation. | Control group |

Every turn is logged to `data/logs/<session_id>.jsonl` (student text, reasoning
assessment, action taken, latency, mastery), which is the raw data for analysing
explanation-driven learning.

---

## Project structure

```
GenAI_Calculus_Tutor/
├── backend/
│   ├── main.py        # FastAPI app + endpoints
│   ├── generator.py   # AI content generation (2.1) + auto-grading
│   ├── socratic.py    # Socratic agent + explain-to-unlock policy (2.2)
│   ├── llm.py         # OpenAI-compatible client (retries + robust JSON)
│   ├── guardrail.py   # blocks "just give me the answer" / prompt injection
│   ├── problems.py    # loads the static problem bank
│   ├── store.py       # in-memory sessions + JSONL event logging
│   ├── schemas.py     # pydantic models
│   └── config.py      # env / paths
├── frontend/
│   └── streamlit_app.py   # two blocks: Practice + Tutor
├── data/
│   ├── problems.json  # 12 seed Calc 1 problems (used by the tutor too)
│   └── logs/          # per-session JSONL logs (gitignored)
├── scripts/           # smoke / api / generation tests + analysis, seeding + log analysis
├── reports/           # generated tables + figures (gitignored)
├── requirements.txt
└── .env               # LLM credentials (gitignored)
```

---

## Setup

1. Create / use a Python environment (Python 3.9+), then install deps:

```bash
pip install -r requirements.txt
```

2. Configure credentials. Copy `.env.example` to `.env` and fill in your key:

```
LLM_BASE_URL=https://api.openlux.ai/v1
LLM_API_KEY=your-api-key-here
LLM_MODEL=gpt-4o-mini
BACKEND_URL=http://localhost:8000
```

> Security note: never commit `.env`. If a key was ever pasted in chat or shared,
> rotate it in the provider dashboard.

---

## Run

Open two terminals.

**Terminal 1 — backend:**

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — frontend:**

```bash
streamlit run frontend/streamlit_app.py
```

Then open the Streamlit URL (default http://localhost:8501). The page is split
left/right:

- **Left (Practice):** choose a topic/type, click **Generate**, answer the
  question, and **Submit** for instant grading.
- **Right (Tutor):** ask anything right away (free chat). To get help on the
  generated question specifically, click **🔗 Link this question to the tutor**
  (left) or **Link question** (right). Use **Free chat** to unlink.

### Student vs instructor view

The page is **student-facing** by default: it hides the experiment internals
(condition, reasoning scores, hint levels) and shows a clean experience with an
encouraging progress bar. The experimental condition is assigned **randomly
behind the scenes** and still recorded in the logs.

To reveal the experimental controls and live metrics (for testing or a demo to
reviewers), open the **instructor view**:

```
http://localhost:8501/?instructor=1
```

---

## API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | liveness + model info |
| `GET` | `/topics` | list of calculus topics |
| `POST` | `/generate` | generate a question (type/topic/difficulty) |
| `POST` | `/grade` | auto-grade a submitted answer |
| `GET` | `/problems` | public seed problem list (no answers) |
| `POST` | `/session/start` | create a tutor session (seed or generated id) |
| `POST` | `/session/{sid}/message` | send a student message, get tutor turn |
| `GET` | `/session/{sid}` | current session state |

Interactive docs at http://localhost:8000/docs.

---

## Tests

With the backend running:

```bash
python -m scripts.smoke_test       # LLM + agent behavior
python -m scripts.api_test         # full conversation over the API
python -m scripts.test_generation  # generate + grade all four question types
```

## Analytics (for the empirical study)

Every turn is logged to `data/logs/<session_id>.jsonl`. To turn those logs into
comparison tables and charts:

```bash
python -m scripts.seed_sessions   # OPTIONAL: generate demo sessions (backend up)
python -m scripts.analyze_logs    # build reports/ tables + figures
```

Outputs land in `reports/`:
- `turns.csv`, `sessions.csv`, `condition_summary.csv`
- `figures/condition_comparison.png` — reasoning quality, explanation length,
  solve rate, final mastery (explain vs control)
- `figures/assessment_distribution.png` — distribution of reasoning quality

Both conditions are *measured* the same way; the only manipulation is whether
the tutor *requires* an explanation before advancing (explain-to-unlock). That
keeps the explain-vs-control comparison fair.

---

## Scope & roadmap

**In this demo (v0.2):** AI content generation in four question types with
auto-grading (2.1), Socratic agent with explain-to-unlock (2.2), two-block
student UI (Practice + Tutor), basic guardrail, LaTeX rendering, per-turn
logging, A/B condition switch.

**Deferred (future work):** automatic problem generation, multimodal input
(handwriting / image / voice), BKT/DKT student modeling, instructor dashboard,
adaptive difficulty, stronger jailbreak detection, and Learnvia integration
(LTI / embed).
