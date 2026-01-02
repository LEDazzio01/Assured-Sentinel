# Makefile for Assured Sentinel
# Provides common development commands

.PHONY: help install demo calibrate dashboard test lint clean

# Default target
help:
	@echo "Assured Sentinel - Available Commands"
	@echo "======================================"
	@echo ""
	@echo "  make install     - Install dependencies"
	@echo "  make demo        - Run offline demo (no API key needed)"
	@echo "  make calibrate   - Run calibration to generate threshold"
	@echo "  make dashboard   - Launch Streamlit dashboard"
	@echo "  make test        - Run unit tests"
	@echo "  make lint        - Run linting (flake8)"
	@echo "  make clean       - Remove generated files"
	@echo ""

# Install dependencies
install:
	pip install -r requirements.txt

# Run offline demo (no API key required)
demo:
	python demo.py

# Run calibration
calibrate:
	python calibration.py

# Launch dashboard
dashboard:
	python -m streamlit run dashboard.py

# Run with LLM (requires Azure OpenAI)
run:
	python run_day5.py

# Run tests
test:
	pytest tests/ -v

# Run tests with coverage
test-cov:
	pytest tests/ --cov=. --cov-report=term-missing --cov-report=html

# Lint code
lint:
	flake8 *.py tests/ --max-line-length=120 --ignore=E501,W503

# Type checking (if mypy is installed)
typecheck:
	mypy *.py --ignore-missing-imports

# Clean generated files
clean:
	rm -f calibration_data.pkl
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -delete

# Full CI check (lint + test)
ci: lint test
	@echo "CI checks passed!"

# Quick verification of a code snippet (usage: make verify CODE="print('hello')")
verify:
	@python -c "from commander import Commander; c = Commander(); print(c.verify('''$(CODE)'''))"
