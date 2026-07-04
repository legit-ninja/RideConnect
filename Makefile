# Makefile — RideConnect dev shortcuts
# Use docker-compose (snap) on this machine if `docker compose` is unavailable.

DOCKER_COMPOSE ?= docker-compose

.PHONY: up up-fresh down build logs doctor dev-split dev-api reset-docker migrate seed shell-api shell-web reset-db

# Start DB + web (API runs on host via make dev-api — required on Snap Docker)
up:
	$(DOCKER_COMPOSE) up -d --no-recreate db web
	@echo "DB + web started. In another terminal run: make dev-api"
	@echo "Then open http://localhost:3000"

# Full rebuild + recreate (requires working Docker stop; may need: sudo snap restart docker)
up-fresh:
	$(DOCKER_COMPOSE) up --build -d db web
	@echo "DB + web started. In another terminal run: make dev-api"

down:
	$(DOCKER_COMPOSE) down

build:
	$(DOCKER_COMPOSE) build

logs:
	$(DOCKER_COMPOSE) logs -f

doctor:
	chmod +x scripts/dev-doctor.sh
	./scripts/dev-doctor.sh

# DB in Docker; API + Next.js on host (recommended on Snap Docker)
dev-split:
	$(DOCKER_COMPOSE) up -d --no-recreate db
	@echo "DB: localhost:5432"
	@echo "Run API:    make dev-api"
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
	@if docker-compose ps api 2>/dev/null | rg -q 'Up'; then \
		$(DOCKER_COMPOSE) exec api pytest; \
	else \
		cd backend && .venv/bin/pytest; \
	fi

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
	$(DOCKER_COMPOSE) up --build -d db web
	@echo "Run: make migrate && make seed && make dev-api"
