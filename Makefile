.PHONY: help install install-dev test test-cov lint format type-check check clean run dry-run install-uv install-dev-uv docker-build docker-run docker-run-dry docker-scan docs-serve docs-build

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

# Fast dependency management with uv
install-uv:
	@command -v uv >/dev/null 2>&1 || { echo "Installing uv..."; curl -LsSf https://astral.sh/uv/install.sh | sh; }
	uv pip install -r requirements.txt

install-dev-uv:
	@command -v uv >/dev/null 2>&1 || { echo "Installing uv..."; curl -LsSf https://astral.sh/uv/install.sh | sh; }
	uv pip install -r requirements.txt
	uv pip install types-requests types-tqdm hypothesis
	pre-commit install

# Docker commands
docker-build:
	docker build -t orst-scrapper:latest .

docker-run:
	docker run --rm -v $(PWD)/data:/app/data -v $(PWD)/reports:/app/reports orst-scrapper:latest

docker-run-dry:
	docker run --rm -v $(PWD)/data:/app/data -v $(PWD)/reports:/app/reports orst-scrapper:latest --dry-run

docker-scan:
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image orst-scrapper:latest

# Documentation
docs-serve:
	mkdocs serve

docs-build:
	mkdocs build

