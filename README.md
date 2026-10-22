# RideConnect

Trust-first marketplace connecting riders with animal owners for verified riding experiences.

## Stack

- **Backend:** FastAPI, PostgreSQL, SQLAlchemy, Alembic
- **Frontend:** Next.js, TypeScript

## Local development

### Quick start (recommended)

```bash
cp .env.example .env
make up          # docker-compose up -d --no-recreate
make doctor      # verify API + web health
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

### If `docker-compose up` fails with "permission denied"

This machine uses **snap Docker**, which can block stopping containers. Symptoms:

```
Error response from daemon: cannot stop container: ... permission denied
```

**Full reset** (run in your terminal):

```bash
sudo snap restart docker
sleep 3
cd rideconnect
docker-compose down
docker-compose up --build -d
```

Or print the same steps: `make reset-docker`

**Workaround without resetting Docker** — run API in Docker, frontend on the host:

```bash
make dev-split
cd frontend && npm run dev
```

Use `docker-compose up -d --no-recreate` (via `make up`) instead of plain `docker-compose up` when containers are already running.

### Default admin login (dev)

Set in `.env`:

```
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=change-me-admin
```

Sign in at http://localhost:3000/login

### Dev seed data

After migrations, load sample users, animals, and listings:

```bash
make up    # start db (+ api/web) if not already running
make migrate
make seed
```

If the `api` container cannot reach `db` (common with snap Docker), `make migrate` and `make seed` automatically fall back to the host using `localhost:5432` while the `db` container is running.

**If login fails with "Is the API running?"** — the API may be down. Start it on the host:

```bash
make dev-api    # terminal 1 — API at http://localhost:8000
```

Ensure `db` is running (`make up` or `docker-compose up -d db`). The Docker `api` service often cannot reach `db` on snap Docker; `make dev-api` avoids that.

All seeded email/password users use password `password123`. See [marketplace-ui.md](docs/marketplace-ui.md) for the full persona login table (riders, owners, dual-role, minor/guardian, friend invites, and booking scenarios).

**Bulk admin-preview accounts** (`bulk.rider.*`, `bulk.owner.*`, `bulk.both.*`) also use `password123` — see [admin-ui.md](docs/admin-ui.md). These populate `/admin/users` pagination and owner animal counts; they are not persona walkthrough accounts.

| Email | Role | Verification |
|-------|------|--------------|
| `both.verified@example.com` | rider + owner | verified |
| `owner.verified@example.com` | owner | verified |
| `rider.verified@example.com` | rider | verified |
| `owner.verified2@example.com` | owner | verified (many listings) |
| `rider.unverified@example.com` | rider | unverified (blocked) |
| `owner.pending@example.com` | owner | pending (blocked from hosting) |
| `minor.rider@example.com` | rider (minor) | unverified |
| `guardian@example.com` | rider + owner | verified |

OAuth-only dev user: `oauth.only@example.com` (no password; remains unverified).

Set `SEED_DEV_DATA=true` or `ENVIRONMENT=development` in `.env` for the seed script to run.

### Environment variables

| Template | Copy to | Used by |
|----------|---------|---------|
| `.env.example` | `.env` | Backend / Docker |
| `frontend/.env.local.example` | `frontend/.env.local` | Next.js (host dev) |

**Never commit** `.env` or `.env.local`.

## Deploy (dev / prod on 192.168.3.3)

Same pipeline as Underdog Unlimited and Sound Strategy: local build → rsync → Apache TLS proxy → systemd. RideConnect adds FastAPI + system PostgreSQL.

| Env | Web | API | Ports | DB |
|-----|-----|-----|-------|-----|
| local | http://localhost:3000 | http://localhost:8000 | — | Docker |
| dev | https://dev.phantomequestrian.com | https://api.dev.phantomequestrian.com | 3010 / 8010 | `rideconnect` |
| prod | https://phantomequestrian.com | https://api.phantomequestrian.com | 3009 / 8009 | `rideconnect_prod` |

Sibling Node ports on this host: Sound Strategy 3003/3004, PMA 3005/3006, Underdog Unlimited 3007/3008.

```bash
cp deploy/config.example.sh deploy/config.sh
cp deploy/env.example.sh deploy/env.dev.sh
cp deploy/env.example.sh deploy/env.prod.sh
# Fill secrets; use 127.0.0.1:5432 and correct public URLs per target
chmod +x scripts/server-setup.sh scripts/server-db.sh scripts/deploy.sh scripts/extract-logo.sh
./scripts/server-setup.sh
./scripts/server-db.sh dev
./scripts/server-db.sh prod
./scripts/extract-logo.sh
./scripts/deploy.sh dev
./scripts/deploy.sh prod
```

See `.cursor/skills/deploy/SKILL.md` and `.cursor/skills/local-dev/SKILL.md`.

## License

Copyright © 2026 Phantom Equestrian. All rights reserved.

See [LICENSE](LICENSE).

## Documentation

- [Data model](docs/data-model.md)
- [Design system](docs/design-system.md) — tokens, themes, spacing
- [Public listings & invite links spec](docs/specs/public-listings-and-invite-links-spec.md)
- [Data model additions](docs/specs/data-model-additions.md)
- [Anti-trafficking safety rules](docs/safety/anti-trafficking.md)
- [Admin UI](docs/admin-ui.md)
- [Marketplace UI](docs/marketplace-ui.md)
