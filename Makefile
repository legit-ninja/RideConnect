# Makefile — RideConnect dev shortcuts
# Use docker-compose (snap) on this machine if `docker compose` is unavailable.

DOCKER_COMPOSE ?= docker-compose

.PHONY: up up-fresh down build logs doctor dev-split dev-api reset-docker migrate seed shell-api shell-web reset-db

# Start stack without recreating running containers (avoids snap Docker stop bugs)
up:
	$(DOCKER_COMPOSE) up -d --no-recreate

# Full rebuild + recreate (requires working Docker stop; may need: sudo snap restart docker)
up-fresh:
	$(DOCKER_COMPOSE) up --build -d

down:
	$(DOCKER_COMPOSE) down

build:
	$(DOCKER_COMPOSE) build

logs:
	$(DOCKER_COMPOSE) logs -f

doctor:
	chmod +x scripts/dev-doctor.sh
	./scripts/dev-doctor.sh

# API + DB in Docker; Next.js on host (recommended when snap Docker blocks container stop)
dev-split:
	$(DOCKER_COMPOSE) up -d --no-recreate db api
	@echo "API: http://localhost:8000/health"
	@echo "Run frontend: cd frontend && npm run dev"

# API on host when Docker api cannot reach db (snap Docker networking)
dev-api:
	chmod +x scripts/run-api-host.sh
	./scripts/run-api-host.sh

# Recover from snap Docker permission-denied (run manually — needs sudo password)
reset-docker:
	@echo "Run these commands in your terminal:"
	@echo "  sudo snap restart docker"
	@echo "  sleep 3"
	@echo "  cd $(CURDIR) && $(DOCKER_COMPOSE) down && $(DOCKER_COMPOSE) up --build -d"

test-backend:
	$(DOCKER_COMPOSE) exec api pytest

test-frontend:
	$(DOCKER_COMPOSE) exec web npm test

migrate:
	chmod +x scripts/db-task.sh
	./scripts/db-task.sh migrate

seed:
	chmod +x scripts/db-task.sh
	./scripts/db-task.sh seed

shell-api:
	$(DOCKER_COMPOSE) exec api /bin/sh

shell-web:
	$(DOCKER_COMPOSE) exec web /bin/sh

reset-db:
	$(DOCKER_COMPOSE) down -v
	$(DOCKER_COMPOSE) up --build -d
