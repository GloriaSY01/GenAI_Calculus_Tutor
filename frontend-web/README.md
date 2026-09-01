# Teacher Dashboard — Vite + React

A modern rewrite of the **teacher-facing** app (previously Streamlit) using
**Vite + React + ECharts**. The student app and the FastAPI backend are unchanged.

## Why this exists

The original teacher UI lived in `frontend/teacher_app.py` + `frontend/teacher/*.py`
(Streamlit). This module reimplements the same features as a real single-page web
app so the UI can be styled and customized freely:

- **Overview** — KPI cards, key insights, tutor-vs-solo comparison, topic health
- **Diagnose** — accuracy by knowledge point, reasoning-quality distribution, practice results
- **Assign** — problem-set builder, quick templates, scheduled-assignment list (create/delete)
- **Assistant** — natural-language Q&A over class data

Extras: light/dark theme, 中文 / English toggle, responsive layout.

## Run

```bash
cd frontend-web
npm install
npm run dev        # http://localhost:5175
```

The dev server proxies `/api/*` to the FastAPI backend (default
`http://localhost:8000`). Start the backend as usual:

```bash
uvicorn backend.main:app --reload
```

Override the backend URL if needed:

```bash
VITE_BACKEND_URL=http://localhost:8000 npm run dev
```

> If the backend is unreachable, the UI automatically falls back to demo data
> (marked with a `● demo data` pill) so you can still preview everything.

## Build

```bash
npm run build      # outputs dist/
npm run preview
```

## Backend endpoints used

| Method | Path                 | Purpose                              |
|--------|----------------------|--------------------------------------|
| GET    | `/analytics/class`   | KPIs, topic accuracy, reasoning dist |
| POST   | `/analytics/ask`     | Data-assistant Q&A                   |
| GET    | `/topics`            | Topic list for the assignment form   |
| GET    | `/assignments`       | List scheduled assignments           |
| POST   | `/assignments`       | Create an assignment                 |
| DELETE | `/assignments/{id}`  | Delete an assignment                 |

## Structure

```
frontend-web/
├── index.html
├── vite.config.js          # /api proxy -> FastAPI
├── src/
│   ├── main.jsx
│   ├── App.jsx             # sidebar nav + routing + theme/lang
│   ├── i18n.jsx            # zh / en copy (ported from i18n.py)
│   ├── api.js              # backend calls + mock fallback
│   ├── mock.js             # demo data (mirrors backend shape)
│   ├── styles/theme.css    # design system (light/dark tokens)
│   ├── components/
│   │   ├── ui.jsx          # Card, Kpi, Badge, Bar, Chart, ...
│   │   └── hooks.js        # useAsync / useAnalytics
│   └── pages/
│       ├── Overview.jsx
│       ├── Diagnose.jsx
│       ├── Assign.jsx
│       └── Assistant.jsx
```

## Notes on the migration

- The **backend did not change** — React calls the same REST endpoints the
  Streamlit app used.
- The old Streamlit teacher files (`frontend/teacher_app.py`, `frontend/teacher/`)
  can be retired once this is adopted; they are left in place for reference.
- State that Streamlit handled implicitly (`st.session_state`, `?instructor=1`)
  is now explicit React state / routing.
