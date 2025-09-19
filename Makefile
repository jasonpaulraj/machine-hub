# Machine Hub Development Makefile

.PHONY: help dev-up dev-down dev-logs dev-rebuild dev-clean prod-up prod-down

# Default target
help:
	@echo "Machine Hub Development Commands:"
	@echo "  make dev-up      - Start development environment with hot reload"
	@echo "  make dev-down    - Stop development environment"
	@echo "  make dev-logs    - Show logs from all development services"
	@echo "  make dev-rebuild - Force rebuild and restart development services"
	@echo "  make dev-clean   - Stop services and clean up volumes/images"
	@echo "  make prod-up     - Start production environment"
	@echo "  make prod-down   - Stop production environment"

# Development commands
dev-up:
	@echo "Starting development environment..."
	docker-compose -f docker-compose.dev.yml up --build -d

dev-down:
	@echo "Stopping development environment..."
	docker-compose -f docker-compose.dev.yml down

dev-logs:
	@echo "Showing logs for development environment..."
	docker-compose -f docker-compose.dev.yml logs -f

dev-rebuild:
	@echo "Rebuilding development environment..."
	docker-compose -f docker-compose.dev.yml down
	docker-compose -f docker-compose.dev.yml up --build -d --force-recreate

dev-clean:
	@echo "Cleaning up development environment..."
	docker-compose -f docker-compose.dev.yml down -v
	docker system prune -f

# Production commands
prod-up:
	@echo "Starting production environment..."
	docker-compose up --build -d

prod-down:
	@echo "Stopping production environment..."
	docker-compose down

# Quick aliases
up: dev-up
down: dev-down
logs: dev-logs
rebuild: dev-rebuild
clean: dev-clean