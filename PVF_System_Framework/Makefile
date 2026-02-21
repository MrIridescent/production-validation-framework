.PHONY: help install lint test coverage format security validate build docker-build docker-up docker-down clean

help:
	@echo "Production Validation Framework - Build Automation"
	@echo "===================================================="
	@echo "Available commands:"
	@echo "  make install        - Install dependencies"
	@echo "  make lint          - Run linting checks (flake8)"
	@echo "  make format        - Format code with black"
	@echo "  make test          - Run unit tests"
	@echo "  make coverage      - Generate coverage report"
	@echo "  make security      - Run security checks (bandit)"
	@echo "  make validate      - Run production readiness validation"
	@echo "  make build         - Build the package"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-up     - Start Docker containers"
	@echo "  make docker-down   - Stop Docker containers"
	@echo "  make clean         - Remove build artifacts"

install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -e .

lint:
	flake8 src/ validation_framework/ --count --select=E9,F63,F7,F82 --show-source --statistics

format:
	black src/ validation_framework/

test:
	pytest tests/ -v

coverage:
	pytest tests/ -v --cov=validation_framework --cov-report=html --cov-report=term-missing

security:
	bandit -r src/ validation_framework/ -f json -o bandit-report.json
	safety check --json

validate:
	python src/AAA_PLUS_READINESS_VALIDATION.py

gaps-analysis:
	python src/GAPS_ANALYSIS_TOOL.py

all-validations: validate gaps-analysis

build:
	python setup.py sdist bdist_wheel

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

clean:
	rm -rf build/ dist/ *.egg-info
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache/ .coverage htmlcov/ bandit-report.json

production-check: clean lint test coverage security validate
	@echo "✅ All production checks passed!"
