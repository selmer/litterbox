# ===================== Stage 1: Build frontend =====================
FROM node:22-slim AS frontend-builder

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ===================== Stage 2: Python app =====================
FROM python:3.13-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Copy built frontend from stage 1
COPY --from=frontend-builder /frontend/dist ./frontend/dist

# Run migrations then start the server
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000