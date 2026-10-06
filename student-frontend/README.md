# Student Frontend (React, port 5173)

Vite + React client for **both** the student workspace and the teacher dashboard.
KaTeX renders mathematics; ECharts renders teacher charts.

This is the student application. The teacher dashboard runs separately from
`teacher-frontend/teacher_app.py` on port 8503. Do not start Streamlit under `teacher-frontend/` unless you
are looking at the old prototype.

## Run

Backend first (repo root):

```bash
python -m uvicorn backend.main:app --reload --reload-dir backend --host 127.0.0.1 --port 8000
```

Then:

```bash
cd student-frontend
npm install
npx vite --host 127.0.0.1
```

PowerShell:

```powershell
$env:VITE_BACKEND_URL="http://127.0.0.1:8000"
npm run dev
```

Open http://127.0.0.1:5173. Switch **Teacher / Student** at the bottom of the
sidebar. Use `127.0.0.1` rather than `localhost` on Windows so the `/api` proxy
hits IPv4 uvicorn.

If the backend is unreachable, teacher pages fall back to demo data (`● demo data`).
`POST /localize` has no demo fallback.

## Layout

```
student-frontend/
├── vite.config.js              # /api and /textbook-assets → 127.0.0.1:8000
├── src/
│   ├── App.jsx                 # role switch, teacher routes
│   ├── pages/StudentWorkspace.jsx
│   ├── pages/student/
│   ├── pages/Overview.jsx      # teacher
│   ├── pages/Diagnose.jsx
│   ├── pages/Assign.jsx
│   └── pages/Assistant.jsx
```
