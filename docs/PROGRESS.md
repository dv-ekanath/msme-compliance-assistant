# Progress vs. Proposal — AI-Powered MSME Compliance Assistant (SIH 2026)

Source of truth for the target vision: `docs/SIH_MSME_Compliance_Assistant.docx`
(SIH 2026 Round 1 submission — the "Compliance Digital Twin" proposal).
This file tracks how much of that proposal is actually built, verified
against the current codebase (151 backend tests passing as of this check).

## What the proposal promises

A Compliance Digital Twin: a live, per-business model of an MSME's
registrations, employees, licenses, obligations, filings, and risk,
continuously synced against a regulatory knowledge graph, with:

- Predictive compliance (forecast obligations from growth signals)
- Voice + vernacular input (WhatsApp-style voice notes → structured updates)
- Regulation-change watchdog agent (monitors gazettes/circulars, flags affected MSMEs)
- Explainable, citation-grounded recommendations (RAG over the bare act/circular)
- Human-in-the-loop submission (AI drafts, human/CA approves before filing)
- Full audit trail

Architecture layers per the doc: Entry → Orchestration → Core data (rules
engine, digital twin store, knowledge graph + RAG) → AI reasoning (LLM +
guardrails) → Action (document AI, workflow automation, reminders) →
Assurance (risk engine, human/CA approval) → Closure (submission + audit).

## Completed

### Phase 0 — Foundation ✅
- Repo scaffold: FastAPI backend, React 19 + Vite + TS + Tailwind v4 frontend
- Docker Compose (Postgres 16 + pgvector)
- Alembic migrations wired up
- LLM provider abstraction (`app/llm/`) — mandatory indirection, `mock` provider default, no API key required to run
- Seed-data structure and health-check endpoints

### Phase 1 — Core Digital Twin + Rules Engine ✅
- Data model: User, Business, Registration, Regulation, Obligation, Filing (`0001_initial_schema` migration)
- Deterministic Rules Engine (`app/rules/`) — 9 rules covering GST, Udyam, EPF, ESI, Shops & Establishment, Professional Tax, reading configurable thresholds from seeded `Regulation` rows (not hardcoded)
- 6 regulations seeded from real government sources (gst.gov.in, udyamregistration.gov.in, epfindia.gov.in, esic.gov.in, state Shops & Establishment Act, professional tax)
- API modules: `/business`, `/registrations`, `/twin`, `/obligations`, `/compliance`
- Frontend: Onboarding, Dashboard, Checklist screens
- No RAG/LLM involved in the twin/rules path — this decision path is fully explainable/deterministic, matching the proposal's "defensible to judges" requirement
- 48 backend tests

### Phase 2 — RAG + Compliance Copilot ✅
- `RegulatoryDocument` / `RegulatoryChunk` models + `0003` migration
- `EmbeddingProvider` abstraction (`app/embeddings/`) — `local` (sentence-transformers, on-box) default, `mock` for tests
- Deterministic chunker preserving section boundaries
- pgvector cosine-distance retrieval (with SQLite Python-fallback for tests)
- Citation-grounded `ComplianceCopilotService` + `POST /copilot/ask/{id}` (`app/rag/copilot.py`)
- Post-generation citation guardrail — every answer flagged `grounded` / `confidence` / `requires_verification`
- Frontend Copilot chat page
- Demo corpus caveat (see below): every seeded regulatory document is `status=demo`, never `verified` — so `requires_verification` is *correctly* always `True` right now
- 38 new tests (88 total, all currently passing)
- LLM still never decides applicability here either — it explains/cites, the rules engine already decided

### Phase 3 — Predictive Risk + Watchdog ✅
- Heuristic (non-ML) risk scoring: `app/rules/risk.py` scores every APPLICABLE `Obligation` 0–100 from due-date urgency × obligation-type weight (PAYMENT/FILING > RENEWAL/REGISTRATION) × frequency weight (MONTHLY > ANNUALLY), exposed as `risk_band`/`risk_reason` model properties — no migration needed, reused the `Obligation.risk_score` column reserved since Phase 1
- Growth-forecast alerts (`app/services/alerts.py`): predicts an obligation before it's applicable — flags when `employee_count` is within a configurable window of a regulation's `min_employee_count` threshold (EPF's 20, ESI's 10), generic over any regulation carrying that key
- Watchdog scan (`app/watchdog/scanner.py`): real `httpx` GET against each seeded `Regulation.source_url`, sha256 content hash compared to the last stored hash, per-URL errors caught without aborting the scan
- Scheduled via in-process APScheduler (`app/watchdog/scheduler.py`), gated off during tests so the FastAPI TestClient's lifespan doesn't spin up a background job per test; `POST /watchdog/scan` for manual/demo triggering
- Affected-business matching reuses the existing Business→Obligation→Regulation relational structure (the "knowledge graph" per project rules) as a plain join — no new graph store, no LLM
- New `Alert` model + `0004_watchdog_and_alerts` migration, `/alerts` API, Alerts frontend page, risk-band badges on Checklist
- 22 new backend tests (110 total)
- **Verified against real infrastructure, not just mocks:** ran a live scan against real Postgres and the actual seeded government URLs. It surfaced real-world flakiness exactly as designed to tolerate — `epfindia.gov.in` timed out, `esic.gov.in` failed TLS certificate verification, `udyamregistration.gov.in` returned 403 — and the scan continued past all three, correctly checked the remaining regulations, and created real `Alert` rows for detected changes with accurate affected-business counts.

### Phase 4 — Voice/Vernacular + Document AI ✅
- Browser voice input (`frontend/src/hooks/useSpeechRecognition.ts`) via the Web Speech API into the Compliance Copilot chat — English/Hindi toggle, mic button hidden (not disabled) on unsupported browsers, frontend-only
- Real OCR document extraction for 3 document types (GST Certificate, Udyam Certificate, PAN Card), each mapping onto an existing `Business` column with zero migration
- `OCRProvider` abstraction (`app/ocr/`) mirroring the LLM/embedding pattern exactly — real default is EasyOCR (on-box, no API key, downloads a model on first use), `mock` for tests
- Field extraction is deterministic regex over well-known Indian ID formats (`app/ocr/extraction.py`, GSTIN/PAN/Udyam) — not LLM-based
- `POST /documents/extract` takes no DB session and persists nothing — the mandatory human-review step is enforced architecturally: extracted values only populate editable Onboarding form fields and are never saved until the user completes the existing submit
- 20 new backend tests (130 total)
- **Verified against real infrastructure, not just mocks:** ran real EasyOCR inference against real synthetic images (not just the mock provider). It surfaced a genuine, reproducible risk and a genuine, reproducible limitation, both handled correctly:
  - EasyOCR's default progress bar crashes with `UnicodeEncodeError` on Windows' default console codepage during the first-run model download — found, root-caused by reading EasyOCR's source, and fixed with `verbose=False` before it could bite on demo day
  - OCR misread "0000" as "OOOO" on a rendered test image (a well-known digit/letter ambiguity) — the system correctly did *not* silently accept the wrong value; it returned a "please verify manually" warning and left the field for human review, which is the designed behavior, not a bug

### Phase 5 — Human-in-the-loop + Submission + Audit ✅
- Real JWT auth (`app/core/security.py`: bcrypt + PyJWT) — plain functions, not a provider abstraction, since there's only ever one real implementation (nothing to swap via an env var, unlike LLM/embeddings/OCR)
- **Scoping decision, made explicitly rather than silently**: auth is required only on the new Filing actions (create/approve/reject/submit), not retrofitted onto Phases 1-4's routes. Every existing route had zero auth concept; retrofitting would have broken 130 passing tests and every existing frontend flow for a requirement the Phase 5 checklist line didn't ask for. Skipping auth entirely would have made "human-in-the-loop approval" a hollow UI label, so it gates exactly the actions where "who did this" carries legal/safety weight
- CA and ADMIN form one "reviewer" role via `require_reviewer` (`app/api/deps.py`) — not a 3-tier permissions framework
- Filing state machine (`app/services/filings.py`): `DRAFT -> APPROVED|REJECTED -> (if APPROVED) SUBMITTED`, each transition 409s from the wrong starting state; draft documents are deterministic templates built from the Digital Twin, not LLM-generated
- Mock submission disclosure (`Filing.mock`/`mock_notice`) is a computed model property present on every read of a SUBMITTED filing — not just the one-time submit response — so it survives a page reload or a direct API call, not just a UI label
- `AuditLog` model + `log_audit_event()` (`app/services/audit.py`) wired into all 4 Filing transitions, user registration, and retrofitted into Business/Registration create+update, Obligation status PATCH, Alert acknowledge, and `/compliance/evaluate` — system-triggered events (watchdog alerts, login attempts) are intentionally not logged, since an audit log's value is "which human did what"
- New migration `0005` (users password + audit_logs table) plus bugfix migration `0006`
- Login/Filings frontend pages, "Prepare Filing" button on Checklist gated to `obligation_type === 'filing' && applicability === 'applicable'`
- 22 new backend tests (151 total)
- **Verified against real infrastructure, not just mocks, and it caught a real bug:** running the live draft-generation flow against real Postgres (not SQLite) hit `StringDataRightTruncation` — `filings.document_ref` was a `VARCHAR(500)` inherited from Phase 1's schema-readiness column, but the real deterministic draft text routinely exceeds 500 chars. SQLite doesn't enforce VARCHAR length, so all 149 tests passed before this was caught — the same class of bug migration `0002` fixed for `regulations.version` in Phase 1. Fixed with bugfix migration `0006` (VARCHAR(500) → Text) plus a regression test. Also caught in the same live run: the mock-submission notice was only present in the immediate `POST /submit` response, not on a later `GET /filings` — fixed by making it a computed property on the model instead of a one-time schema field, with a regression test confirming a re-fetched submitted filing still carries the disclosure.

## Not yet started

### Phase 6 — Polish + Demo script ⬜
- Seeded MSME personas
- Scripted live demo flow
- Deployment
- Offline fallback

## Gaps against the proposal worth flagging

- Both of the proposal's headline differentiators are now built: the
  regulation-change watchdog agent (Phase 3) and voice input (Phase 4).
  Voice input is narrower than the original proposal's vision though —
  it's browser Web Speech API into the Copilot chat, not a WhatsApp voice
  bot that converts speech into structured Digital Twin updates; that
  fuller vision was intentionally descoped in CLAUDE.md's Phase 4 line.
- **OCR is English-only for now** (`OCR_LANGUAGES=en` default) — sufficient
  for extracting GSTIN/PAN/Udyam numbers (always Latin script/digits on
  real certificates regardless of surrounding document language), but not
  Hindi-language document text generally. Configurable via `OCR_LANGUAGES`
  if that's ever needed.
- **Regulatory corpus is demo-only**, not verified against live government
  sources beyond the seed files' `source_url` — this is disclosed
  correctly via `SourceStatus.DEMO`, not hidden, but it means every Copilot
  answer today is marked `requires_verification=True` and isn't yet
  citation-grade for a real filing.
- **Auth is narrowly scoped** (see Phase 5 above) — Business/Registration/
  Obligation/Alert/Copilot/Watchdog/Documents routes remain unauthenticated,
  matching Phases 1-4's existing behavior. This is a deliberate, disclosed
  scope cut, not an oversight: a hackathon demo app, not a production
  multi-tenant system with per-business access control.
- **Government portal submission is still fully mocked** (correctly, per
  rule 5 — no real government portal access exists to integrate with),
  but the workflow *around* it (draft generation, human review, approval,
  audit trail) is now real, working code, not a stub.

## Recommended next step

Commit the completed Phase 2 through Phase 5 work (currently uncommitted,
last commit is `64accce`), then proceed to Phase 6 per the project's
phase-gating rule (don't start a later phase until the current one is
confirmed complete).
