.PHONY: install run clean lint format test docker-build docker-run help

# Variables
PYTHON := python
PIP := pip
DOCKER := docker

help:
	@echo "WebSite to Android & iOS App - Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make install      Install dependencies"
	@echo "  make run          Run the application"
	@echo "  make lint         Run linting checks"
	@echo "  make format       Format code with black and isort"
	@echo "  make test         Run tests"
	@echo "  make clean        Clean build artifacts"
	@echo "  make docker-build Build Docker image"
	@echo "  make docker-run   Run in Docker container"

install:
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install -e ".[dev]"

run:
	$(PYTHON) main.py

lint:
	flake8 . --max-line-length=120 --exclude=.git,__pycache__,bin,output,venv
	mypy . --ignore-missing-imports

format:
	black . --line-length 120
	isort . --profile black

test:
	pytest tests/ -v

clean:
	@echo "Cleaning build artifacts..."
	rm -rf __pycache__ .pytest_cache .mypy_cache
	rm -rf output/*.apk output/app output/WebApp_iOS
	rm -rf build dist *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Done."

docker-build:
	$(DOCKER) build -t website2app:latest .

docker-run:
	$(DOCKER) run -it --rm -v $(PWD)/output:/app/output website2app:latest
