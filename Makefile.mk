# Makefile for intelliTest

.PHONY: help install setup-dev api create-auth-state test clean

VENV_DIR := venv
PYTHON := $(VENV_DIR)/bin/python

help:
	@echo "Available commands:"
	@echo "  install           - Creates a virtual environment and installs Python dependencies."
	@echo "  setup-dev         - Runs 'install' and also installs frontend dependencies and Playwright browsers. The one-stop shop for setup."
	@echo "  api               - Runs the backend FastAPI server with auto-reload."
	@echo "  create-auth-state - (Legacy) Runs the interactive script to manually save a login session."
	@echo "  test              - Runs the pytest test suite."
	@echo "  clean             - Removes generated files, virtual environment, and cache."

install:
	@echo "Creating virtual environment..."
	python3 -m venv $(VENV_DIR)
	@echo "Installing Python dependencies from requirements.txt..."
	$(PYTHON) -m pip install -r requirements.txt
	@echo "Python installation complete. Activate with: source $(VENV_DIR)/bin/activate"

setup-dev: install
	@echo "Installing Playwright browsers..."
	$(PYTHON) -m playwright install
	@echo "Installing frontend dependencies..."
	(cd frontend && npm install)
	@echo "Full development setup complete."

api:
	@echo "Starting FastAPI server at http://127.0.0.1:8000"
	$(PYTHON) -m uvicorn src.intelli_test.api:app --reload

create-auth-state:
	@echo "Running authentication state creation script..."
	$(PYTHON) -m src.intelli_test.utilities.create_auth_state

test:
	@echo "Running pytest suite..."
	$(PYTHON) -m pytest

clean:
	@echo "Cleaning up..."
	rm -rf $(VENV_DIR)
	rm -rf tests/__pycache__ src/intelli_test/utilities/__pycache__
	rm -f auth_state.json auth_creation_settings.json
	(cd frontend && rm -rf node_modules build)
	@echo "Cleanup complete."