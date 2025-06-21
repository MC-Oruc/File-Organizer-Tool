.PHONY: help install install-dev test test-unit test-integration test-gui test-all clean lint format security check coverage run

help:			## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:		## Install the package
	pip install -e .

install-dev:		## Install the package with development dependencies
	pip install -r requirements-dev.txt
	pip install -e .

test:			## Run all tests
	pytest tests/ -v

test-unit:		## Run only unit tests
	pytest tests/ -v -m "unit"

test-integration:	## Run only integration tests
	pytest tests/ -v -m "integration"

test-gui:		## Run only GUI tests
	pytest tests/ -v -m "gui"

test-slow:		## Run slow tests
	pytest tests/ -v -m "slow"

test-all:		## Run all tests with coverage
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing

clean:			## Clean up generated files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

lint:			## Run linting tools
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=120 --statistics

format:			## Format code
	black .
	isort .

format-check:		## Check code formatting
	black --check --diff .
	isort --check-only --diff .

security:		## Run security checks
	bandit -r . -x tests/
	safety check

check:			## Run all checks (lint, format, security)
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) security

coverage:		## Generate coverage report
	pytest tests/ --cov=. --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

run:			## Run the application in GUI mode
	python main.py

run-cli:		## Show CLI help
	python main.py --help

# Example CLI commands
example-organize:	## Example: Organize files in a directory
	@echo "Example usage: python main.py /path/to/directory -s '-' -r -v -y"

example-reverse:	## Example: Reverse organization
	@echo "Example usage: python main.py /path/to/directory --reverse -y"

example-export:		## Example: Export directory tree
	@echo "Example usage: python main.py /path/to/directory --export-tree --output tree.txt"

# Development workflow targets
dev-setup:		## Set up development environment
	$(MAKE) install-dev
	pre-commit install

dev-test:		## Run development tests (unit + integration)
	$(MAKE) test-unit
	$(MAKE) test-integration

dev-check:		## Run all development checks
	$(MAKE) check
	$(MAKE) test-all

build:			## Build distribution packages
	python setup.py sdist bdist_wheel

upload-test:		## Upload to test PyPI
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

upload:			## Upload to PyPI
	twine upload dist/*

# Locale management
check-locales:		## Check locale file consistency
	pytest tests/test_localization.py::TestLocaleFiles -v

# Documentation
docs:			## Generate documentation (if implemented)
	@echo "Documentation generation not implemented yet"

# Docker targets (for future use)
docker-build:		## Build Docker image
	@echo "Docker build not implemented yet"

docker-test:		## Run tests in Docker
	@echo "Docker test not implemented yet" 