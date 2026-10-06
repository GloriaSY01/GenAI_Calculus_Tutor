# GenAI Calculus Tutor

*English | [中文](README.zh-CN.md)*

A grounded GenAI learning companion for **Calculus 1**. Students work from
Gilbert Strang's *Calculus* (MIT OpenCourseWare): read a cited concept page,
practise on textbook or generated items, and talk to a Socratic tutor that
asks for reasoning instead of revealing the answer. Instructors see class-level
analytics from the same interaction log.

Built with **FastAPI** (backend), **Vite + React** (student app under
`student-frontend/`), and **Streamlit** (teacher dashboard under
`teacher-frontend/teacher_app.py`). The teacher interface is Streamlit-only; the React
app does not contain teacher views.

---

## Student and teacher views

Two separate processes on fixed local ports, linked to each other:

- **Student (React, :5173):** textbook contents, concept page, free practice /
  challenge mode, in-question tutor, and favourites. Chinese/English toggle;
  textbook prose can follow the UI language.
- **Teacher (Streamlit, :8503):** Overview, Diagnose, Assign, Assistant, with
  behaviour-based class analytics.

The tutor still supports two conditions (`explain` vs `control`). Explain-to-unlock
requires a justification before the next hint; control gives progressive hints
without that gate. Both are scored the same way. Turns are logged to
`data/logs/<session_id>.jsonl`.

---

## Project structure

```
GenAI_Calculus_Tutor/
├── backend/                 # FastAPI: RAG, generate/grade, tutor, analytics
├── student-frontend/           # Student app: Vite + React, port 5173
├── teacher-frontend/           # Teacher dashboard: Streamlit, port 8503
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
cd student-frontend
npm install
```

On Windows, if `npm install` fails with `EPERM` on the global cache:

```powershell
npm config set cache "$env:LOCALAPPDATA\npm-cache"
npm install
```

---

## Run

Three processes run on fixed loopback ports:

| Process | URL | Stack |
|---|---|---|
| Backend API | http://127.0.0.1:8000 | FastAPI |
| Teacher dashboard (the only one) | http://127.0.0.1:8503/?lang=en | Streamlit |
| Student app | http://127.0.0.1:5173 | React + Vite |

### One command (recommended)

After installing dependencies (`pip install -r requirements.txt` and
`npm install` inside `student-frontend/`), run from the repo root:

```bash
scripts/run_dev.sh
```

It starts the backend, teacher, and student in order and stops all three on
`Ctrl+C`. Override ports with `BACKEND_PORT / TEACHER_PORT / STUDENT_PORT`.

### Manual (three terminals)

From the repo root.

**Terminal 1 — backend:**

```bash
python -m uvicorn backend.main:app --reload --reload-dir backend --host 127.0.0.1 --port 8000
```

`--reload-dir backend` keeps Vite's `node_modules` from restarting the API.
Use `127.0.0.1`, not `localhost`, on Windows (Node 18+ may resolve `localhost`
to IPv6 while uvicorn listens on IPv4).

**Terminal 2 — teacher:**

```bash
python -m streamlit run teacher-frontend/teacher_app.py \
  --server.address 127.0.0.1 --server.port 8503
```

**Terminal 3 — student:**

```bash
cd student-frontend
npm run dev -- --host 127.0.0.1
```

### Switching roles

- Student → teacher: open **Settings** (top right) and click **Teacher**; it opens
  `http://127.0.0.1:8503/?lang=<current language>`.
- Teacher → student: the **Student** link at the top returns to
  `http://127.0.0.1:5173/`.

The two are separate processes and ports, but the links are fixed and never point
at another version. The teacher interface is Streamlit-only; there are no React
teacher pages in `student-frontend`.

If the backend is down, the dashboard shows an explicit "cannot connect" message
rather than demo results. Translation requests (`POST /localize`) fail visibly too.

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
