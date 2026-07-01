# RideConnect

Trust-first marketplace connecting riders with animal owners for verified riding experiences.

## Stack

- **Backend:** FastAPI, PostgreSQL, SQLAlchemy, Alembic
- **Frontend:** Next.js, TypeScript

## Local development

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for frontend)

### Backend + database

```bash
cp .env.example .env
docker compose up --build
```

API runs at http://localhost:8000. Health check: http://localhost:8000/health

### Frontend

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Frontend runs at http://localhost:3000.

## Environment variables

Templates live in the repo; secrets stay local only:

| Template | Copy to | Used by |
|----------|---------|---------|
| `.env.example` | `.env` | Backend / Docker |
| `frontend/.env.local.example` | `frontend/.env.local` | Next.js frontend |

**Never commit** `.env`, `.env.local`, or any file containing real credentials. Stripe keys, JWT secrets, and production database URLs belong only in your local env files.

## License

Copyright © 2026 Phantom Equestrian. All rights reserved.

This repository is public for transparency. Viewing source code does not grant any license to use, fork, or deploy this software commercially. See [LICENSE](LICENSE) for full terms.

## Documentation

- [Data model](docs/data-model.md)

## Project context

Product requirements and MVP scope live in the workspace Cursor rules at `.cursor/rules/rideconnect-mvp.mdc`.
