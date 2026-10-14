FROM node:20-alpine AS frontend

WORKDIR /build/student-frontend
COPY student-frontend/package*.json ./
RUN npm ci
COPY student-frontend/ ./
ARG VITE_TEACHER_DASHBOARD_URL
ENV VITE_TEACHER_DASHBOARD_URL=${VITE_TEACHER_DASHBOARD_URL}
RUN npm run build

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY requirements-deploy.txt ./
RUN pip install --no-cache-dir -r requirements-deploy.txt

COPY backend/ backend/
COPY data/ data/
COPY --from=frontend /build/student-frontend/dist/ student-frontend/dist/

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
