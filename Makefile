.PHONY: help install install-dev test test-cov lint format type-check check clean run dry-run

# Default target
help:
	@echo "ORST Dictionary Scraper - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  install      Install production dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo ""
	@echo "Quality:"
	@echo "  lint         Run Ruff linter"
	@echo "  format       Format code with Ruff"
	@echo "  type-check   Run MyPy type checker"
	@echo "  check        Run all quality checks (lint + format + type-check)"
	@echo ""
	@echo "Testing:"
	@echo "  test         Run tests"
	@echo "  test-cov     Run tests with coverage report"
	@echo ""
	@echo "Run:"
	@echo "  run          Run the scraper (full update)"
	@echo "  dry-run      Run the scraper in dry-run mode"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean        Remove build artifacts and caches"

# Setup
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install types-requests types-tqdm
	pre-commit install

# Quality checks
lint:
	ruff check scripts/ tests/

format:
	ruff format scripts/ tests/

type-check:
	mypy scripts/

check: lint format type-check
	@echo "All checks passed!"

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=scripts --cov-report=term-missing --cov-report=html

# Run the scraper
run:
	python update_royin_dictionary.py

dry-run:
	python update_royin_dictionary.py --dry-run --verbose

# Clean up
clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache
	rm -rf scripts/__pycache__ tests/__pycache__
	rm -rf htmlcov .coverage coverage.xml
	rm -rf build dist *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
