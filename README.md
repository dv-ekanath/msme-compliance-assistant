# AI-Powered MSME Compliance Assistant — SIH 2026

A Compliance Digital Twin for MSMEs: per-business regulatory state (registrations,
obligations, filings, risk) kept in sync with a regulatory knowledge graph, with
explainable, citation-grounded recommendations.

**Status: Phase 5 — Human-in-the-loop + Submission + Audit.** A business can
be onboarded, its Digital Twin retrieved, and a deterministic (non-LLM)
Rules Engine evaluates 9 real compliance rules against it. A Compliance
Copilot answers free-text questions ("Why does GST apply to me?", "When is
my next filing due?"), grounded entirely in retrieved regulatory evidence
(pgvector semantic search) and the business's Digital Twin — every legal
claim is cited back to a source, and the LLM never decides applicability
(the Rules Engine does). A heuristic (non-ML) risk score is computed for
every applicable obligation, growth-forecast alerts predict obligations
before they're applicable, and an in-process watchdog scans each
regulation's official source for changes. Onboarding can extract
GSTIN/Udyam Number/PAN from an uploaded document photo via real on-box OCR
(with a mandatory human-review step before anything is saved), and the
Copilot chat accepts English/Hindi voice input via the browser's Web Speech
API. A "Prepare Filing" action on the Checklist generates a deterministic
draft (not LLM-written) that a logged-in CA/reviewer must approve before a
clearly-labeled mock submission — real JWT auth gates exactly this
approval workflow (see "Auth" below for why it isn't retrofitted onto
every other route), and an audit log records who did what across the
app's state-changing actions. Only Phase 6 (demo polish, seeded personas,
deployment, offline fallback) remains — see `CLAUDE.md` for the phase plan.

## Stack

- **Backend:** FastAPI (Python), SQLAlchemy 2.x, Alembic
- **Frontend:** React 19 + Vite + TypeScript + Tailwind CSS v4
- **Database:** PostgreSQL 16 with the `pgvector` extension (via Docker)
- **LLM:** provider-abstracted — defaults to a mock provider, no API key required
- **Embeddings:** provider-abstracted — defaults to local sentence-transformers
  (all-MiniLM-L6-v2, 384-dim), no API key/credits required
- **OCR:** provider-abstracted — defaults to local EasyOCR, no API key/credits required
- **Scheduling:** APScheduler (in-process, no Celery/Redis) for the watchdog scan
- **Auth:** JWT (PyJWT + bcrypt) — no provider abstraction, there's only one real implementation

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
`filings` (`0001`), widens `regulations.version` (`0002`), and adds
`regulatory_documents` + `regulatory_chunks` with a pgvector `embedding`
column (`0003`).

### Seed the regulatory knowledge base + RAG demo corpus

```
cd backend
python -m seed.load_regulations             # 6 regulations (GST, Udyam, EPF, ESI, S&E, Professional Tax)
python -m seed.load_regulatory_documents     # chunks + embeds the RAG demo corpus (downloads the
                                              # embedding model on first run, then it's cached)
```
Both are idempotent — safe to re-run after editing a seed file.

### Try it end-to-end

```
curl -X POST http://localhost:8000/api/v1/business -H "Content-Type: application/json" -d "{\"name\":\"Test Co\",\"sector\":\"trading\",\"state\":\"Maharashtra\",\"registration_type\":\"proprietorship\",\"turnover_band\":\"5cr_50cr\",\"employee_count\":45}"
# copy the returned "id", then:
curl -X POST http://localhost:8000/api/v1/compliance/evaluate/<business_id>
curl http://localhost:8000/api/v1/twin/<business_id>
curl -X POST http://localhost:8000/api/v1/copilot/ask/<business_id> -H "Content-Type: application/json" -d "{\"question\":\"What is the GST registration threshold?\"}"
```

### Backend tests

```
cd backend
pip install -r requirements-dev.txt
pytest
```
Runs fully offline against an in-memory SQLite DB (no Docker/Postgres, no
model downloads needed) — 151 tests covering the API, the Digital Twin, all
9 rules, chunking, retrieval, the citation guardrail, the Copilot, risk
scoring, growth forecasting, the watchdog scan, alerts, document
extraction, auth, and the Filing approval workflow, all using the
deterministic mock LLM/embedding/OCR providers.

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
- `/copilot/:businessId` — ask free-text compliance questions (voice input
  supported); answers show a grounded/not-grounded badge, a confidence
  level, a verification warning when relevant, and the exact regulatory
  sources cited (with links)
- `/alerts/:businessId` — regulation-change and growth-forecast alerts
- `/filings/:businessId` — the approval queue: prepare a filing from an
  applicable filing obligation on the Checklist, then a logged-in
  CA/reviewer approves/rejects/submits it here
- `/login` — log in or register; see "Auth" below for demo accounts

## Embedding provider: local (default) vs. mock (tests)

- `backend/app/embeddings/base.py` — the `EmbeddingProvider` interface.
- `backend/app/embeddings/local_provider.py` — default (`EMBEDDING_PROVIDER=local`),
  sentence-transformers running on-box, no API key/credits. Downloads
  `all-MiniLM-L6-v2` (~90MB) from Hugging Face on first use, then caches it.
- `backend/app/embeddings/mock_provider.py` — deterministic, dependency-free,
  used by the test suite (`EMBEDDING_PROVIDER=mock`) so tests never need to
  load a model.
- `backend/app/embeddings/factory.py` — `get_embedding_provider()` picks the
  implementation based on the `EMBEDDING_PROVIDER` env var. `EMBEDDING_DIMENSION`
  is the single source of truth for the pgvector column width — change the
  model, and this validates the new dimension matches (or fails loudly).

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

## OCR provider: EasyOCR (default) vs. mock (tests)

- `backend/app/ocr/base.py` — the `OCRProvider` interface.
- `backend/app/ocr/easyocr_provider.py` — default (`OCR_PROVIDER=easyocr`),
  EasyOCR running on-box, no API key/credits. Downloads its detection +
  recognition models (~100MB) on first use, then caches them — this can
  take several minutes depending on your connection, so it's worth
  pre-warming once rather than hitting it cold during a live demo:
  ```
  python -c "import easyocr; easyocr.Reader(['en'], gpu=False, verbose=False)"
  ```
  (`verbose=False` matters here, not just for quieter output — EasyOCR's
  default progress bar prints a Unicode character that crashes with
  `UnicodeEncodeError` on Windows' default console codepage.)
- `backend/app/ocr/mock_provider.py` — deterministic, dependency-free, used
  by the test suite (`OCR_PROVIDER=mock`) so tests never need to run real
  inference.
- `backend/app/ocr/extraction.py` — pure, deterministic regex extraction of
  GSTIN/Udyam Number/PAN from OCR-recognized text (no LLM/ML). Used by
  `POST /api/v1/documents/extract`, which never writes to the database —
  the Onboarding page shows extracted fields in editable inputs and only
  saves them when the user completes the form, enforcing the human-review
  step by construction rather than by convention.

## Auth: JWT, scoped to the Filing approval workflow

`backend/app/core/security.py` (bcrypt password hashing + PyJWT tokens) and
`backend/app/api/deps.py` (`get_current_user`, `require_reviewer`) are real,
working auth — not a stub. **It's deliberately not required on every
route.** Business/Registration/Obligation/Alert/Copilot/Watchdog/Documents
stay open, exactly as they were in Phases 1-4; only creating, approving,
rejecting, and submitting a `Filing` require a login, and only
approve/reject/submit require the CA/admin ("reviewer") role. See
`docs/PROGRESS.md`'s Phase 5 entry for the full reasoning — in short,
retrofitting auth onto every existing route would have been Phase-5 scope
creep into Phase 1-4 territory and broken every existing frontend flow, but
skipping auth entirely would make "human-in-the-loop approval" a hollow UI
label. It gates exactly the actions where "who did this" carries legal
weight.

Two demo accounts exist for testing/demo purposes:
```
cd backend
python -m seed.create_demo_users
```
Creates (idempotently) `owner@demo.msme` / `ca@demo.msme`, both with
password `demo1234`. Log in as the CA account to approve/reject/submit a
filing prepared by the owner.

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
│   │   ├── rag/                   # Phase 2: RAG + Compliance Copilot
│   │   │   ├── chunking.py        # Deterministic, section-boundary-preserving chunker
│   │   │   ├── ingestion.py       # Seed JSON -> chunked, embedded DB rows
│   │   │   ├── retrieval.py       # pgvector search (SQLite Python-fallback for tests)
│   │   │   ├── context.py         # Digital Twin -> prompt-ready text
│   │   │   ├── prompts.py         # Grounded system/user prompt construction
│   │   │   ├── guardrail.py       # Post-generation citation validation
│   │   │   └── copilot.py         # Orchestrates the above -> CopilotAnswer
│   │   ├── embeddings/            # Provider-agnostic embedding abstraction
│   │   ├── ocr/                   # Provider-agnostic OCR abstraction + extraction.py
│   │   ├── watchdog/               # Phase 3: scanner.py + APScheduler scheduler.py
│   │   ├── schemas/                # Pydantic request/response models
│   │   ├── api/
│   │   │   ├── deps.py            # Phase 5: get_current_user / require_reviewer
│   │   │   └── routes/
│   │   │       ├── health.py / business.py / registrations.py
│   │   │       ├── twin.py / obligations.py / compliance.py / copilot.py
│   │   │       └── alerts.py / watchdog.py / documents.py / auth.py / filings.py
│   │   └── llm/                   # Provider-agnostic LLM abstraction
│   ├── alembic/versions/          # 0001 initial schema, 0002 widen version col,
│   │                               #   0003 regulatory_documents + regulatory_chunks,
│   │                               #   0004 watchdog scan state + alerts,
│   │                               #   0005 users password + audit_logs,
│   │                               #   0006 widen filings.document_ref
│   ├── seed/
│   │   ├── load_regulations.py            # Idempotent regulation seed loader
│   │   ├── load_regulatory_documents.py   # Idempotent RAG corpus loader (chunks + embeds)
│   │   ├── create_demo_users.py           # Idempotent owner/CA demo account creator
│   │   ├── regulations/*.json             # GST, Udyam, EPF, ESI, S&E, Professional Tax
│   │   └── regulatory_documents/*.json    # Demo excerpts derived from the above (see its README)
│   ├── tests/                     # 151 tests, run offline against SQLite
│   ├── requirements.txt / requirements-dev.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/                 # Onboarding, Dashboard, Checklist, Copilot, Alerts, Filings, Login, Landing
│   │   ├── components/Nav.tsx
│   │   ├── hooks/useSpeechRecognition.ts  # Web Speech API wrapper (English/Hindi)
│   │   ├── lib/api.ts             # Typed fetch client for the backend API (attaches JWT when present)
│   │   ├── lib/auth.ts            # login/register, token storage
│   │   └── types.ts               # Mirrors backend schemas/enums
│   ├── package.json
│   └── .env.example
├── infra/postgres/init/           # pgvector extension bootstrap
├── docker-compose.yml             # Postgres + pgvector
├── .env.example                   # Docker Compose credentials
└── CLAUDE.md                      # Project instructions / phase plan
```

## Phase plan

See `CLAUDE.md` for the full phased implementation plan (Phases 0–5 are
complete; Phase 6 is demo polish, seeded personas, deployment, offline
fallback).
