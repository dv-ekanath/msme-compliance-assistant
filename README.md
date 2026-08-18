# AI-Powered MSME Compliance Assistant — SIH 2026

A Compliance Digital Twin for MSMEs: per-business regulatory state (registrations,
obligations, filings, risk) kept in sync with a regulatory knowledge graph, with
explainable, citation-grounded recommendations.

**Status: Phase 0 — Foundation.** Repo scaffold, backend/frontend skeletons, DB
config, and the LLM provider abstraction are in place. No feature logic (rules
engine, RAG, voice, watchdog, approvals, etc.) exists yet — see `CLAUDE.md` for
the phase plan.

## Stack

- **Backend:** FastAPI (Python), SQLAlchemy 2.x, Alembic
- **Frontend:** React 19 + Vite + TypeScript + Tailwind CSS v4
- **Database:** PostgreSQL 16 with the `pgvector` extension (via Docker)
- **LLM:** provider-abstracted (see below) — defaults to a mock provider, no API key required

## Prerequisites

- Python 3.11+ (tested on 3.14)
- Node.js 20+ (tested on 24)
- Docker Desktop (for Postgres) — only needed once you want a real database;
  the backend and frontend run without it

## 1. Clone / open the project

```
cd msme-compliance-assistant
```

## 2. Start the database (Docker)

```
docker compose up -d
```

This starts Postgres 16 with `pgvector` on `localhost:5432`, using the
credentials in the root `.env` (copy `.env.example` to `.env` first if it
doesn't exist yet — see below). The `vector` extension is created
automatically on first init via `infra/postgres/init/001_enable_pgvector.sql`.

> Docker Desktop must be **running** first (`docker info` should succeed).
> If you don't have it running yet, the backend still starts fine — only
> `/api/v1/health/db` will report `unreachable` until Postgres is up.

## 3. Backend setup

```
cd backend
python -m venv .venv

# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (Git Bash):
source .venv/Scripts/activate

pip install -r requirements.txt
copy .env.example .env      # PowerShell; on Bash: cp .env.example .env

uvicorn app.main:app --reload --port 8000
```

Backend is now at http://localhost:8000 — interactive docs at
http://localhost:8000/docs.

Verify:
```
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/health/llm
curl http://localhost:8000/api/v1/health/db
```

### Database migrations (Alembic)

No tables exist yet (Phase 0 has no domain models). Once Postgres is running:
```
cd backend
alembic upgrade head
```
This is currently a no-op (no migrations exist yet) but confirms the DB
connection and Alembic wiring both work end-to-end.

## 4. Frontend setup

In a second terminal:
```
cd frontend
npm install
copy .env.example .env      # PowerShell; on Bash: cp .env.example .env
npm run dev
```

Frontend is now at http://localhost:5173. It calls the backend's
`/api/v1/health` endpoint on load and shows a live "Backend online/offline"
badge in the header.

## LLM provider: mock vs. real Claude API

The Anthropic API is **not** wired to your Claude Pro subscription — Claude
Pro (used here in Claude Code) does not grant API credits for this
application. The app is built so it never needs one during development:

- `backend/app/llm/base.py` — the `LLMProvider` interface. All app code
  depends only on this.
- `backend/app/llm/mock_provider.py` — default (`LLM_PROVIDER=mock`), pure
  offline echo responses, no network calls, no key needed.
- `backend/app/llm/anthropic_provider.py` — real Claude API. Only this file
  imports the `anthropic` SDK, and only when actually selected.
- `backend/app/llm/factory.py` — `get_llm_provider()` picks the
  implementation based on the `LLM_PROVIDER` env var.

To switch to the real API later:
```
pip install anthropic
```
then in `backend/.env`:
```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```
No other code changes needed.

## Project layout

```
msme-compliance-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI app entrypoint
│   │   ├── core/
│   │   │   ├── config.py          # Settings (env vars)
│   │   │   └── database.py        # SQLAlchemy engine/session
│   │   ├── api/routes/
│   │   │   └── health.py          # /health, /health/db, /health/llm
│   │   ├── llm/                   # Provider-agnostic LLM abstraction
│   │   │   ├── base.py
│   │   │   ├── mock_provider.py
│   │   │   ├── anthropic_provider.py
│   │   │   └── factory.py
│   │   └── models/
│   │       └── base.py            # SQLAlchemy declarative base (no tables yet)
│   ├── alembic/                   # Migrations (env.py wired to app config)
│   ├── seed/regulations/          # Regulatory knowledge base seed structure
│   │   ├── schema.json
│   │   └── _template.sample.json  # placeholder, not verified legal content
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── main.tsx / App.tsx
│   │   ├── pages/Dashboard.tsx    # Landing shell + backend status badge
│   │   └── lib/api.ts             # fetch wrapper for the backend API
│   ├── package.json
│   └── .env.example
├── infra/postgres/init/           # pgvector extension bootstrap
├── docker-compose.yml             # Postgres + pgvector
├── .env.example                   # Docker Compose credentials
└── CLAUDE.md                      # Project instructions / phase plan
```

## Phase plan

See `CLAUDE.md` for the full phased implementation plan (Phase 0 is complete;
Phases 1–6 build out the Rules Engine, RAG/Knowledge Graph, predictive risk,
watchdog, voice, and human-in-the-loop approval workflow).
