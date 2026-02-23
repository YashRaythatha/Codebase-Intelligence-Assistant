# Codebase Intelligence Assistant
# Backend in backend/, frontend in frontend/

PYTHON ?= python
PIP ?= $(PYTHON) -m pip

.PHONY: setup lint test run-api run-web run-all

setup:
	$(PIP) install -e .
	@echo "Copy .env.example to .env and set OPENAI_API_KEY"

lint:
	$(PYTHON) -m ruff check backend
	$(PYTHON) -m black --check backend

test:
	$(PYTHON) -m pytest backend/tests -v

run-api:
	$(PYTHON) -m app.main

run-web:
	cd frontend && npm run dev

run-all:
	@echo "Run in two terminals:"
	@echo "  Terminal 1: make run-api"
	@echo "  Terminal 2: make run-web"
