# Backend image – build from repo root: docker build -f backend/docker/Dockerfile .
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY backend/ ./backend/
RUN pip install --no-cache-dir -e . && mkdir -p data

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["python", "-m", "app.main"]
