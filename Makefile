.PHONY: help install test run-app run-cli clean

help:
	@echo "Agents-Claude - Available Commands"
	@echo "=================================="
	@echo "make install    - Install dependencies"
	@echo "make test       - Run test suite"
	@echo "make run-app    - Run Streamlit app"
	@echo "make run-cli    - Run CLI in interactive mode"
	@echo "make clean      - Clean cache and temp files"

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=src --cov-report=html

run-app:
	streamlit run src/app.py

run-cli:
	python src/cli.py interactive

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
