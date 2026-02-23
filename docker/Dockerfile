# Codebase Intelligence Assistant - backend image
FROM python:3.11-slim

WORKDIR /app

# Dependencies and package install (packages live under backend/)
COPY pyproject.toml ./
COPY backend/ ./backend/
RUN pip install --no-cache-dir -e . && \
    mkdir -p data

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# Run from /app so data/ is /app/data when mounted
CMD ["python", "-m", "app.main"]
