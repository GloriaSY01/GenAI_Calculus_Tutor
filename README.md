# GenAI Calculus Tutor

*English | [中文](README.zh-CN.md)*

A grounded GenAI learning companion for **Calculus 1**. Students work from
Gilbert Strang's *Calculus* (MIT OpenCourseWare): read a cited concept page,
practise on textbook or generated items, and talk to a Socratic tutor that
asks for reasoning instead of revealing the answer. Instructors see class-level
analytics from the same interaction log.

Built with **FastAPI** (backend) and **Vite + React** (student and teacher in
one app). The older Streamlit files under `frontend/` are not the current UI.

---

## Student and teacher views

One app, switched in the sidebar:

- **Student:** textbook contents, concept page, free practice / challenge mode,
  in-question tutor, and favourites. Chinese/English toggle; textbook prose can
  follow the UI language.
- **Teacher:** Overview, Diagnose, Assign, Assistant. Charts use ECharts.

The tutor still supports two conditions (`explain` vs `control`). Explain-to-unlock
requires a justification before the next hint; control gives progressive hints
without that gate. Both are scored the same way. Turns are logged to
`data/logs/<session_id>.jsonl`.

---

## Project structure

```
GenAI_Calculus_Tutor/
├── backend/                 # FastAPI: RAG, generate/grade, tutor, analytics
├── frontend-web/            # Vite + React (current UI)
├── frontend/                # Streamlit prototype (not used at runtime)
├── data/textbook/mit-calculus/
├── data/chroma/             # generated index (gitignored)
├── data/logs/               # session JSONL (gitignored)
├── scripts/                 # ingest, seed, smoke tests
├── tests/
├── requirements.txt
└── .env                     # LLM credentials (gitignored)
```

---

## Setup

1. Python 3.9+ (this repo is typically run in conda env `yolo8`):

```bash
pip install -r requirements.txt
```

2. Build the Chroma index from the bundled MIT chapters (once, or after textbook
   updates). Embedding weights download on first run if missing:

```bash
python -m scripts.ingest_mit --chapters 1 2 3 4 5 6 7 8
```

MinerU parsing is only needed if you regenerate text from the PDFs. The
repository already includes curated passages, exercises, figures, and TOC.

3. Copy `.env.example` to `.env` and set `LLM_API_KEY`. Do not commit `.env`.

4. Frontend dependencies:

```bash
cd frontend-web
npm install
```

On Windows, if `npm install` fails with `EPERM` on the global cache:

```powershell
npm config set cache "$env:LOCALAPPDATA\npm-cache"
npm install
```

---

## Run

Two terminals, from the repo root.

**Terminal 1 — backend:**

```bash
python -m uvicorn backend.main:app --reload --reload-dir backend --host 127.0.0.1 --port 8000
```

`--reload-dir backend` keeps Vite's `node_modules` from restarting the API.
Use `127.0.0.1`, not `localhost`, on Windows (Node 18+ may resolve `localhost`
to IPv6 while uvicorn listens on IPv4).

**Terminal 2 — frontend:**

```bash
cd frontend-web
npx vite --host 127.0.0.1
```

Or, in PowerShell, pin the proxy target explicitly:

```powershell
cd frontend-web
$env:VITE_BACKEND_URL="http://127.0.0.1:8000"
npm run dev
```

Open http://127.0.0.1:5175 (or the port Vite prints). Switch **Teacher / Student**
at the bottom of the sidebar.

If the backend is down, teacher pages may show a `● demo data` badge. Translation
requests (`POST /localize`) do not use demo text: they fail visibly instead.

Optional teacher-dashboard seed data:

```bash
python scripts/seed_demo_logs.py
```

---

## API

Interactive docs: http://127.0.0.1:8000/docs

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | liveness, model, RAG status |
| `GET` | `/catalog` | textbook table of contents |
| `GET` | `/concept` | RAG concept card with citations |
| `POST` | `/generate` | generate a practice item |
| `POST` | `/grade` | server-side grading |
| `POST` | `/session/start` | start a tutor session |
| `POST` | `/session/{sid}/message` | one tutor turn |
| `POST` | `/localize` | display-only translation |
| `GET` | `/analytics/class` | class-level KPIs |
| `POST` | `/analytics/ask` | teacher assistant |

---

## Tests

```bash
python -m pytest -q
python -m scripts.evaluate_agent
```

With the backend running:

```bash
python -m scripts.smoke_test
python -m scripts.api_test
python -m scripts.test_generation
```

---

## Textbook attribution

Excerpts from Gilbert Strang's *Calculus*, MIT OpenCourseWare, CC BY-NC-SA 4.0
(Fall 2017, chapters 1–8). Parsed assets and the Chroma index are not committed.
