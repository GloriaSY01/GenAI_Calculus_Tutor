# Backend and textbook connection (2026-09-21)

The student workspace uses the existing FastAPI APIs for the catalog, textbook content, question generation, grading, favorites and question-local tutor. Vite now proxies both `/api` and `/textbook-assets` to `http://127.0.0.1:8000` by default. `VITE_BACKEND_URL` can override this target.

## Start locally on Windows

Run these in two terminals from the repository root.

Backend:
```powershell
conda activate yolo8
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Frontend:
```powershell
cd frontend-web
npm.cmd run dev -- --host 127.0.0.1 --port 5175 --strictPort
```

Open http://127.0.0.1:5175/ and choose a chapter, then Textbook. Allow the backend to finish loading the embedding model before refreshing the page. Existing textbook files and the Chroma index are reused; no ingestion is needed for the current checkout. Model credentials remain in the root .env file.

## Verified

- Backend health: RAG ready, 171 indexed chunks and 51 sections.
- Catalog: 8 chapters. All listed sections return textbook content.
- Presentation content: 330 blocks and 188 unique available illustrations; all illustration URLs returned HTTP 200.
- Textbook question generation: HTTP 200 with a textbook source citation.
- Question-local tutor: actual Chinese model reply with retrieved textbook citations. Verification uses the separate integration-check student/class identifiers.
- Browser: chapter 7 textbook text, LaTeX formulas and illustration links display through the frontend proxy.

## Current limits

Textbook presentation blocks and indexed retrieval chunks are different representations, so their counts differ. Textbook notes and curated exercise stems remain in the source language where translations are absent. Challenge pass criteria are still a frontend preview; progress is stored in this browser. Generated questions are stored in backend memory, so questions saved before a backend restart may need a new round before grading or asking the tutor.
