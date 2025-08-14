# Makefile for intelliTest

.PHONY: help install api create-auth-state test clean

VENV_DIR := venv
PYTHON := $(VENV_DIR)/bin/python

help:
	@echo "Available commands:"
	@echo "  install           - Creates a virtual environment and installs dependencies."
	@echo "  api               - Runs the FastAPI server."
	@echo "  create-auth-state - Runs the interactive script to save a login session."
	@echo "  test              - Runs the pytest test suite."
	@echo "  clean             - Removes generated files and cache."

install:
	@echo "Creating virtual environment..."
	python3 -m venv $(VENV_DIR)
	@echo "Installing project in editable mode..."
	$(PYTHON) -m pip install -e .
	@echo "Installation complete. Activate with: source $(VENV_DIR)/bin/activate"

api:
	@echo "Starting FastAPI server at http://127.0.0.1:8000"
	$(PYTHON) -m uvicorn intelli_test.api:app --reload

create-auth-state:
	@echo "Running authentication state creation script..."
	$(PYTHON) -m intelli_test.utilities.create_auth_state

test:
	@echo "Running pytest suite..."
	$(PYTHON) -m pytest