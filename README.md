# AI-Powered MSME Compliance Assistant — SIH 2026

A Compliance Digital Twin for MSMEs: per-business regulatory state (registrations,
obligations, filings, risk) kept in sync with a regulatory knowledge graph, with
explainable, citation-grounded recommendations.

**Status: Phase 1 — Compliance Digital Twin + Rules Engine.** A business can be
onboarded, its Digital Twin retrieved, and a deterministic (non-LLM) Rules
Engine evaluates 9 real compliance rules against it, producing explainable,
citation-backed obligations shown in the frontend checklist. RAG, voice,
watchdog, predictive scoring, auth, and the approval workflow are not built
yet — see `CLAUDE.md` for the phase plan.

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

Once Postgres is running:
```
cd backend
alembic upgrade head
```
Creates `users`, `businesses`, `registrations`, `regulations`, `obligations`,
`filings` (see `alembic/versions/0001_initial_schema.py`).

### Seed the regulatory knowledge base

The Rules Engine won't run until its 6 regulations (GST, Udyam, EPF, ESI,
Shops & Establishment, Professional Tax) are loaded:
```
cd backend
python -m seed.load_regulations
```
Idempotent — safe to re-run after editing a file in `seed/regulations/`.

### Try it end-to-end

```
curl -X POST http://localhost:8000/api/v1/business -H "Content-Type: application/json" -d "{\"name\":\"Test Co\",\"sector\":\"trading\",\"state\":\"Maharashtra\",\"registration_type\":\"proprietorship\",\"turnover_band\":\"5cr_50cr\",\"employee_count\":45}"
# copy the returned "id", then:
curl -X POST http://localhost:8000/api/v1/compliance/evaluate/<business_id>
curl http://localhost:8000/api/v1/twin/<business_id>
```

### Backend tests

```
cd backend
pip install -r requirements-dev.txt
pytest
```
Runs fully offline against an in-memory SQLite DB (no Docker/Postgres
needed) — 48 tests covering the API, the Digital Twin, and positive/negative
cases for all 9 rules.

## 4. Frontend setup

In a second terminal:
```
cd frontend
npm install
copy .env.example .env      # PowerShell; on Bash: cp .env.example .env
npm run dev
```

Frontend is now at http://localhost:5173:
- `/onboarding` — create a business profile, flag any existing registrations,
  and immediately run the Rules Engine
- `/dashboard/:businessId` — the Digital Twin: profile, registrations,
  compliance-health summary, upcoming deadlines
- `/checklist/:businessId` — every obligation with its reason, source
  regulation, and due-date status, filterable by All / Due soon / Overdue / Completed

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
│   │   ├── core/                  # Settings, SQLAlchemy engine/session
│   │   ├── domain/
│   │   │   ├── enums.py           # Shared enums (sector, turnover band, etc.)
│   │   │   └── facts.py           # BusinessFacts -- the Digital Twin's factual core
│   │   ├── models/                # SQLAlchemy: User, Business, Registration,
│   │   │   │                      #   Regulation, Obligation, Filing
│   │   ├── rules/                 # Deterministic Rules Engine (no LLM)
│   │   │   ├── base.py / types.py / engine.py / registry.py
│   │   │   ├── gst.py / udyam.py / epf.py / esi.py
│   │   │   └── shops_establishment.py / professional_tax.py
│   │   ├── services/
│   │   │   ├── twin.py            # Digital Twin assembly + summary
│   │   │   └── compliance.py      # Rules Engine orchestration + obligation upsert
│   │   ├── schemas/                # Pydantic request/response models
│   │   ├── api/routes/
│   │   │   ├── health.py / business.py / registrations.py
│   │   │   └── twin.py / obligations.py / compliance.py
│   │   └── llm/                   # Provider-agnostic LLM abstraction (unused so far)
│   ├── alembic/versions/0001_initial_schema.py
│   ├── seed/
│   │   ├── load_regulations.py    # Idempotent seed loader
│   │   └── regulations/*.json     # GST, Udyam, EPF, ESI, S&E, Professional Tax
│   ├── tests/                     # 48 tests, run offline against SQLite
│   ├── requirements.txt / requirements-dev.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/                 # Onboarding, Dashboard, Checklist, Landing
│   │   ├── components/Nav.tsx
│   │   ├── lib/api.ts             # Typed fetch client for the backend API
│   │   └── types.ts               # Mirrors backend schemas/enums
│   ├── package.json
│   └── .env.example
├── infra/postgres/init/           # pgvector extension bootstrap
├── docker-compose.yml             # Postgres + pgvector
├── .env.example                   # Docker Compose credentials
└── CLAUDE.md                      # Project instructions / phase plan
```

## Phase plan

See `CLAUDE.md` for the full phased implementation plan (Phases 0–1 are
complete; Phases 2–6 build out RAG/Knowledge Graph, predictive risk,
watchdog, voice, and the human-in-the-loop approval workflow).
