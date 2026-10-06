#!/usr/bin/env bash
#
# One-command local dev launcher for GenAI Calculus Tutor.
# Starts all three processes on FIXED loopback ports and tears them down on exit:
#   - FastAPI backend ........ http://127.0.0.1:8000
#   - Teacher dashboard ...... http://127.0.0.1:8503/?lang=zh  (Streamlit)
#   - Student web app ........ http://127.0.0.1:5173            (Vite/React)
#
# Override interpreters if needed:
#   PYTHON=/path/to/python NODEVITE="npm run dev" scripts/run_dev.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# GUI-launched shells may not load ~/.zshrc, where local Node tools live.
if [[ -d "$HOME/.local/bin" ]]; then
  export PATH="$HOME/.local/bin:$PATH"
fi

PYTHON="${PYTHON:-python3}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
TEACHER_PORT="${TEACHER_PORT:-8503}"
STUDENT_PORT="${STUDENT_PORT:-5173}"

export NO_PROXY="127.0.0.1,localhost${NO_PROXY:+,$NO_PROXY}"
export no_proxy="$NO_PROXY"
# The backend is the single source of truth for its own port; Streamlit's api.py
# reads BACKEND_URL (its .env default also matches this).
export BACKEND_URL="http://127.0.0.1:${BACKEND_PORT}"
export VITE_BACKEND_URL="$BACKEND_URL"

pids=()
cleanup() {
  echo
  echo "Stopping dev services..."
  for pid in "${pids[@]:-}"; do kill "$pid" 2>/dev/null || true; done
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "[1/3] backend  -> http://127.0.0.1:${BACKEND_PORT}"
"$PYTHON" -m uvicorn backend.main:app \
  --host 127.0.0.1 --port "$BACKEND_PORT" &
pids+=("$!")

# Give the backend a head start so the dashboard's first load succeeds.
sleep 4

echo "[2/3] teacher  -> http://127.0.0.1:${TEACHER_PORT}/?lang=zh"
"$PYTHON" -m streamlit run teacher-frontend/teacher_app.py \
  --server.address 127.0.0.1 --server.port "$TEACHER_PORT" \
  --server.headless true &
pids+=("$!")

echo "[3/3] student  -> http://127.0.0.1:${STUDENT_PORT}"
( cd student-frontend && npm run dev -- --host 127.0.0.1 --port "$STUDENT_PORT" ) &
pids+=("$!")

echo
echo "All services started. Press Ctrl+C to stop all three."
wait
