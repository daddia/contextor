.PHONY: install dev test lint format clean build optimize serve deploy-aws deploy-vercel help

# Default target
help:
	@echo "Contextor - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install      Install production dependencies"
	@echo "  dev          Install development dependencies"
	@echo "  test         Run tests"
	@echo "  lint         Run linting (ruff + mypy)"
	@echo "  format       Format code (black + ruff)"
	@echo "  clean        Clean build artifacts"
	@echo ""
	@echo "Core Operations:"
	@echo "  optimize     Run contextor optimize (requires --src, --out, --repo, --ref)"
	@echo "  benchmark    Run performance benchmarks"
	@echo ""
	@echo "Server (Phase 2):"
	@echo "  serve        Run MCP server locally"
	@echo "  run-sse      Run MCP server with SSE transport"
	@echo ""
	@echo "Deployment:"
	@echo "  build        Build for deployment"
	@echo "  deploy-aws   Deploy to AWS Lambda"
	@echo "  deploy-vercel Deploy to Vercel"
	@echo ""
	@echo "Examples:"
	@echo "  make dev && make test"
	@echo "  make optimize src=../vendor/nextjs/docs out=../sourcedocs/nextjs repo=vercel/next.js ref=main"
	@echo "  make optimize src=../vendor/nextjs/docs out=../sourcedocs/nextjs repo=vercel/next.js ref=main metrics=metrics.json"
	@echo "  poetry run contextor optimize --src ../vendor/nextjs/docs --out ../sourcedocs/nextjs --project-config nextjs"
	@echo "  poetry run contextor list-projects"

# Development setup
install:
	poetry install --only=main

dev:
	poetry install
	poetry run pre-commit install

# Testing
test:
	poetry run pytest -v

test-cov:
	poetry run pytest --cov=contextor --cov-report=html --cov-report=term

# Code quality
lint:
	poetry run ruff check .
	poetry run mypy contextor/

format:
	poetry run black .
	poetry run ruff check --fix .

# Core operations
optimize:
	@if [ -z "$(src)" ] || [ -z "$(out)" ] || [ -z "$(repo)" ] || [ -z "$(ref)" ]; then \
		echo "Error: Missing required parameters. Usage:"; \
		echo "  make optimize src=<docs_dir> out=<sourcedocs_path> repo=<owner/name> ref=<branch|sha> [topics=<topics>] [metrics=<metrics_path>]"; \
		exit 1; \
	fi
	poetry run contextor optimize --src=$(src) --out=$(out) --repo=$(repo) --ref=$(ref) $(if $(topics),--topics=$(topics)) $(if $(metrics),--metrics-output=$(metrics))

benchmark:
	poetry run contextor benchmark $(if $(budget),--budget=$(budget)) $(if $(output),--output=$(output))

# Server operations (Phase 2)
serve:
	poetry run contextor-server --transport=stdio

run-sse:
	poetry run contextor-server --transport=sse --host=0.0.0.0 --port=8080

# Build and deployment
clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build:
	poetry build

# Export requirements.txt for serverless deployments
export-requirements:
	poetry export -f requirements.txt --output requirements.txt --without-hashes
	poetry export -f requirements.txt --output requirements-dev.txt --without-hashes --with dev

# AWS Lambda deployment
deploy-aws: export-requirements
	./deploy.sh --platform=aws

deploy-aws-prod: export-requirements
	./deploy.sh --platform=aws --env=prod

# Vercel deployment
deploy-vercel: export-requirements
	./deploy.sh --platform=vercel

deploy-vercel-prod: export-requirements
	./deploy.sh --platform=vercel --env=prod

# Docker operations (optional)
docker-build:
	docker build -t contextor-mcp .

docker-run:
	docker run -p 8080:8080 contextor-mcp

# Development utilities
check: lint test
	@echo "All checks passed!"

pre-commit:
	poetry run pre-commit run --all-files

update-deps:
	poetry update

lock:
	poetry lock

# Documentation
docs-serve:
	poetry run mkdocs serve

docs-build:
	poetry run mkdocs build
