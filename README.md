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

## Documentation

- [Data model](docs/data-model.md)

## Project context

Product requirements and MVP scope live in the workspace Cursor rules at `.cursor/rules/rideconnect-mvp.mdc`.
