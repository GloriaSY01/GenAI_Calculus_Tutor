# Railway deployment

This repository deploys as two web services plus one shared PostgreSQL service.

## Architecture

- `student-api`: FastAPI plus the built Vite student app (`Dockerfile`)
- `teacher`: Streamlit teacher dashboard (`Dockerfile.teacher`)
- `Postgres`: shared favorites, assignments, generated questions, tutor sessions,
  learning events, and cross-device study progress

The application still works without `DATABASE_URL` for local development. In
that mode it uses the existing JSON files and browser storage.

## Railway setup

1. Create a Railway project and add PostgreSQL.
2. Add a GitHub service from this repository. Railway detects `Dockerfile`.
   Name it `student-api`, link PostgreSQL's `DATABASE_URL`, and set the health
   check path to `/health`.
3. Generate a public domain for `student-api`.
4. Add a second GitHub service from the same repository. Name it `teacher` and
   set `RAILWAY_DOCKERFILE_PATH=Dockerfile.teacher`.
5. In `teacher`, set `BACKEND_URL` to the private URL of `student-api` and set
   `STUDENT_APP_URL` to the public student URL. Generate a public teacher domain.
6. In `student-api`, set the build variable `VITE_TEACHER_DASHBOARD_URL` to the
   public teacher URL, then redeploy it.
7. Add `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL` only in Railway Variables.
   Never commit the real key to GitHub.

The backend creates its prototype tables automatically on startup. For a later
production phase, add migrations and real authentication before changing table
structures or inviting users outside the project team.

## Identity note

The current interface uses the entered student name plus class as the logical
identity. That is enough for a controlled group demo, but it is not secure
authentication. Before public use, add institutional login or an auth provider
and store an immutable user ID instead of relying on display names.
