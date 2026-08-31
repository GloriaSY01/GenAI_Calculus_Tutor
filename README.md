# GenAI Calculus Tutor

*English | [中文](README.zh-CN.md)*

A grounded GenAI learning prototype for **Calculus 1**. Its focused learning
path has three stages:

1. **Concept:** retrieve an attributed MIT Calculus section and build a cited card.
2. **Practice:** serve verified textbook exercises or generate one of four question formats.
3. **Tutor:** use a Chroma-grounded Socratic agent that asks for reasoning instead
   of revealing the answer.

The system includes input/output guardrails, server-enforced explain-to-unlock,
low-evidence engagement checks, and reproducible evaluation fixtures.

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
│   ├── rag.py         # Chroma retrieval + cited concept cards
│   ├── problems.py    # loads the static problem bank
│   ├── store.py       # in-memory sessions + JSONL event logging
│   ├── schemas.py     # pydantic models
│   └── config.py      # env / paths
├── frontend/
│   └── streamlit_app.py   # Concept → Practice → Tutor focus flow
├── data/
│   ├── problems.json  # 12 seed Calc 1 problems (used by the tutor too)
│   ├── eval/          # deterministic safety/evaluation fixtures
│   ├── textbook/      # MIT metadata, PDFs, curated content and parsed assets
│   ├── chroma/        # generated vector index (gitignored)
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

2. Parse the MIT Fall 2017 chapter PDFs and build the Chroma index:

```bash
mineru -p data/textbook/mit-calculus/pdfs -o data/textbook/mit-calculus/parsed -b pipeline -m txt -f false -t true
python -m scripts.build_mit_toc --write
python -m scripts.ingest_mit --chapters 1 2 3 4 5 6 7 8
```

The repository already contains the eight chapter PDFs and curated metadata.
MinerU output and the generated Chroma index are local artifacts. Configure
`RAG_EMBEDDING_MODEL_DIR` if the embedding model is stored outside its default
location.

3. Configure credentials. Copy `.env.example` to `.env` and fill in your key:

```
LLM_BASE_URL=https://yunwu.ai/v1
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

Then open http://localhost:8501 and follow **Concept → Practice → Tutor**.
Concept, Practice, and Tutor responses expose the MIT sections used for grounding.
Wrong practice answers remain hidden so the student can retry or request a
guided hint.

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
| `GET` | `/concept` | RAG-backed concept card with citations |
| `GET` | `/retrieve` | attributed retrieval results (debug/instructor) |
| `POST` | `/generate` | generate a question (type/topic/difficulty) |
| `POST` | `/grade` | auto-grade a submitted answer |
| `GET` | `/problems` | public seed problem list (no answers) |
| `POST` | `/session/start` | create a tutor session (seed or generated id) |
| `POST` | `/session/{sid}/message` | send a student message, get tutor turn |
| `GET` | `/session/{sid}` | current session state |

Interactive docs at http://localhost:8000/docs.

---

## Tests and evaluation

Deterministic tests do not require a live LLM:

```bash
python -m pytest -q
python -m scripts.evaluate_agent
```

Optional live checks, with the backend running:

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

**Implemented (v0.4):** MIT Calculus Chapters 1–8 in one Chroma collection,
metadata-filtered concept/example retrieval, verified textbook exercises plus
RAG-grounded generation in four formats, cited Socratic tutoring, server-side
grading without wrong-answer leakage, explain-to-unlock, bilingual guardrails,
JSONL events, deterministic tests, and an evaluation script.

**Roadmap (not implemented):** symbolic verification of generated mathematics,
persistent sessions, validated student models (BKT/DKT), multimodal input,
aggregate instructor analytics, adaptive recommendation, and LTI integration.

## Textbook attribution

Textbook excerpts come from Gilbert Strang's *Calculus*, provided by MIT
OpenCourseWare under CC BY-NC-SA 4.0. This project uses the Fall 2017 Chapter
1–8 PDF resources. Indexed chunks retain chapter, section, page, figure, source,
and attribution metadata. Generated parsed assets and indexes are not committed.

## Demo and resume wording

Suggested demo: select **Chain Rule** → inspect a cited concept card → generate
a practice item → show direct-answer blocking → explain a valid step to unlock
the next hint → inspect reasoning, safety, and mastery signals in instructor
view.

Accurate resume summary:

> Built a RAG-grounded Socratic calculus agent using local semantic retrieval
> over eight chapters of MIT Calculus stored in Chroma; implemented server-enforced
> explain-to-unlock, bidirectional anti-leak guardrails, engagement signals,
> and a golden-set evaluation pipeline for retrieval, citation, policy, and
> answer-leak metrics.
