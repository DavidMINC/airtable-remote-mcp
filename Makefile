# Makefile for Airtable Remote MCP Server

.PHONY: help setup run test docker clean deploy check

help: ## Show this help message
	@echo "🛠️  Airtable Remote MCP Server - Development Commands"
	@echo "=============================================="
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development
setup: ## Set up development environment
	python dev.py setup

run: ## Run development server
	python dev.py run

test: ## Run tests
	python dev.py test

check: ## Check environment configuration
	python dev.py check

status: ## Show server status
	python dev.py status

##@ Docker
docker: ## Build and run with Docker
	python dev.py docker

stop: ## Stop Docker container
	python dev.py stop

logs: ## Show Docker logs
	python dev.py logs

clean: ## Clean up Docker resources
	python dev.py clean

##@ Deployment
deploy: ## Deploy to Railway
	python dev.py deploy

secret: ## Generate secure secret key
	python dev.py secret

##@ Utilities
install: ## Install Python dependencies
	pip install -r requirements.txt

format: ## Format code with black (if available)
	@if command -v black >/dev/null 2>&1; then \
		echo "🎨 Formatting code with black..."; \
		black .; \
	else \
		echo "⚠️  black not installed, skipping formatting"; \
	fi

lint: ## Lint code with flake8 (if available)
	@if command -v flake8 >/dev/null 2>&1; then \
		echo "🔍 Linting code with flake8..."; \
		flake8 .; \
	else \
		echo "⚠️  flake8 not installed, skipping linting"; \
	fi

##@ Quick Actions
dev: setup run ## Set up and run development server

prod: docker ## Build and run production Docker container

health: ## Check server health
	@curl -f http://localhost:8000/health || echo "❌ Server not responding"

oauth-test: ## Test OAuth metadata
	@curl -s http://localhost:8000/.well-known/oauth-authorization-server | python -m json.tool

register-test: ## Test client registration
	@curl -X POST http://localhost:8000/oauth/register \
		-H "Content-Type: application/json" \
		-d '{"client_name": "Test Client", "redirect_uris": ["https://example.com/callback"]}' \
		| python -m json.tool
