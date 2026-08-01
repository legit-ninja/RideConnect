---
name: rideconnect-local-dev
description: Set up and troubleshoot local RideConnect development — Docker Postgres, make targets, API on host, frontend env, migrations and seed. Use when starting local dev, fixing snap Docker, migrate/seed, or .env issues.
disable-model-invocation: true
---

# RideConnect local development

## Quick start

```bash
cd /home/jeremy-lee/projects/underdog/phantomequestrian/rideconnect
cp .env.example .env
cp frontend/.env.local.example frontend/.env.local
make up          # db + web containers
make doctor      # health check
make dev-api     # separate terminal — API on :8000 (preferred on snap Docker)
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

## Make targets

| Command | Purpose |
|---------|---------|
| `make up` | Start db + web (`--no-recreate`) |
| `make dev-api` | Uvicorn on host (avoids snap Docker networking) |
| `make migrate` / `make seed` | Alembic + dev fixtures |
| `make doctor` | Probe API/web health |
| `make reset-docker` | Print snap Docker recovery steps |

## Env

| File | Used by |
|------|---------|
| `.env` | Backend / compose |
| `frontend/.env.local` | Next on host (`NEXT_PUBLIC_API_URL=http://localhost:8000`) |

Never commit filled env files. Admin bootstrap: `ADMIN_EMAIL` / `ADMIN_PASSWORD` in `.env`.

## Snap Docker notes

Container→container and container→host often fail. Prefer:

```bash
make up          # db (+ web)
make dev-api     # API on host
# frontend already in compose web, or: cd frontend && npm run dev
```

## Seed personas

After `make migrate && make seed`, password for seeded users is `password123`. See `docs/marketplace-ui.md` and `docs/admin-ui.md`.

## Port conflicts

| Project | Notes |
|---------|-------|
| Local RideConnect API | **8000** |
| Local Postgres (compose) | **5432** |
| Server RideConnect | 3009/3010 web, 8009/8010 api, Postgres **5432** system |

## Common fixes

- **API unreachable from Next**: run `make dev-api`; set `API_INTERNAL_URL` if SSR runs in Docker
- **Permission denied stopping containers**: `sudo snap restart docker` then `make reset-docker` steps
- **Login “Is the API running?”**: start `make dev-api`; confirm `curl localhost:8000/health`
