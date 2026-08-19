# CLAUDE.md

Project instructions for Claude Code sessions working in this repository.

## What this is

AI-Powered MSME Compliance Assistant (SIH 2026) — a Compliance Digital Twin:
a per-business virtual representation of an MSME's regulatory state
(registrations, obligations, filings, risk), kept in sync with a regulatory
knowledge graph, with explainable citation-grounded recommendations via RAG.

Full design rationale, MVP scope decisions, data model, and API list live in
the approved project plan. The condensed version relevant day-to-day:

## Hard rules

1. **LLM/embedding provider abstractions are mandatory.** No application
   code outside `backend/app/llm/` may import the `anthropic` SDK or any
   other vendor LLM SDK directly — go through
   `app.llm.factory.get_llm_provider()` (`backend/app/llm/base.py`).
   Likewise no code outside `backend/app/embeddings/` may import
   `sentence_transformers` directly — go through
   `app.embeddings.factory.get_embedding_provider()`
   (`backend/app/embeddings/base.py`). Both are FastAPI `Depends()`
   parameters in routes (not called directly), so tests can override them.
   Default LLM provider is `mock` (`LLM_PROVIDER=mock`) — the app must run
   fully without an Anthropic API key. Do not assume the developer's Claude
   Pro subscription provides API credits for this app. Default embedding
   provider is `local` (sentence-transformers, on-box, no API key) — tests
   use `mock` (deterministic, no model download).
2. **Don't introduce infra that isn't earning its place.** No Neo4j, no
   LangChain/LangGraph, no Redis/Celery, no separate vector DB — pgvector
   inside the existing Postgres, and a plain relational model for the
   knowledge graph, are sufficient at this project's scale. Revisit only if
   a concrete need appears.
3. **Real corpus, real citations.** Regulation seed data
   (`backend/seed/regulations/`, `backend/seed/regulatory_documents/`) must
   trace back to genuine government sources (gst.gov.in,
   udyamregistration.gov.in, epfindia.gov.in, esic.gov.in, state Shops &
   Establishment Act pages, etc.) with an actual `source_url`. Never
   fabricate regulation text, section numbers, or citations, even as
   placeholder/demo content — mark it explicitly (`SourceStatus.DEMO`, not
   `VERIFIED`) rather than pretending it's authoritative. See
   `backend/seed/regulatory_documents/README.md`.
4. **Deterministic core, LLM for explanation.** The obligation checklist and
   risk scoring must come from the deterministic Rules Engine (Phase 1),
   not the LLM. The LLM's job is explaining/citing, not deciding — this is
   what keeps the system explainable and defensible to judges.
5. **Mock only what requires access we don't have.** Government portal
   submission, payments/challans, and SMS delivery are mocked and must be
   clearly labeled as such in the UI. Everything else (rules engine, RAG,
   digital twin, predictive risk heuristics, watchdog, document extraction,
   human-in-the-loop approval) should be real, working code — not stubs.

## Stack

- Backend: FastAPI (Python), SQLAlchemy 2.x, Alembic, Postgres 16 + pgvector
- Frontend: React 19 + Vite + TypeScript + Tailwind CSS v4
- Embeddings: local sentence-transformers (all-MiniLM-L6-v2, 384-dim), no external API needed
- Scheduling (Phase 3+): APScheduler (in-process), not Celery/Redis
- Auth (Phase 5): JWT, two roles — MSME owner, CA/admin

## Repo layout

See `README.md` "Project layout" section — kept in sync with the actual tree.

## Running locally

See `README.md` for exact setup/run commands (verified working end-to-end:
backend via `uvicorn`, frontend via `npm run dev`, DB via `docker compose up -d`).

## Phase status

- [x] **Phase 0 — Foundation.** Repo scaffold, FastAPI + React skeletons,
      Docker Compose (Postgres+pgvector), Alembic wiring, LLM provider
      abstraction, seed-data structure, health-check endpoints.
- [x] **Phase 1 — Core Twin + Rules Engine.** User/Business/Registration/
      Regulation/Obligation/Filing models + hand-written Alembic migration
      (`0001_initial_schema`), 9-rule deterministic Rules Engine (GST,
      Udyam, EPF, ESI, Shops & Establishment, Professional Tax) reading
      configurable thresholds from seeded Regulation rows, 6 regulations
      seeded from real government sources, `/business` `/registrations`
      `/twin` `/obligations` `/compliance` API modules, Onboarding/
      Dashboard/Checklist frontend screens, 48 backend tests. No RAG/LLM
      involved anywhere in the rules/twin path -- see `app/rules/`.
- [x] **Phase 2 — RAG + Compliance Copilot.** RegulatoryDocument/
      RegulatoryChunk models + migration (`0003`), `EmbeddingProvider`
      abstraction (`local` = sentence-transformers default, `mock` for
      tests), deterministic chunker preserving section boundaries, pgvector
      cosine-distance retrieval (SQLite Python-fallback for tests),
      citation-grounded `ComplianceCopilotService` + `/copilot/ask/{id}`,
      post-generation citation guardrail (grounded/confidence/
      requires_verification), Copilot frontend page, 38 new tests (88
      total). Demo corpus only -- every seeded document is `status=demo`,
      never `verified`, so `requires_verification` is correctly always
      True right now (see `backend/seed/regulatory_documents/README.md`).
      LLM still never decides applicability -- see `app/rag/copilot.py`.
- [x] **Phase 3 — Predictive + Watchdog.** Heuristic (non-ML) risk scoring
      on every APPLICABLE `Obligation` (`app/rules/risk.py`, exposed as
      `risk_score`/`risk_band`/`risk_reason`), growth-forecast alerts that
      predict an obligation before it's applicable (employee count
      approaching EPF/ESI thresholds, `app/services/alerts.py`), a
      watchdog scan (`app/watchdog/scanner.py`) that hashes each seeded
      Regulation's live `source_url` on an in-process APScheduler interval
      (`app/watchdog/scheduler.py`, gated off in tests) and flags content
      changes, affected-business matching via the existing
      Business→Obligation→Regulation join (no new graph store), `Alert`
      model + migration (`0004_watchdog_and_alerts`), `/alerts`
      `/watchdog/scan` API modules, Alerts frontend page + risk badges on
      Checklist, 22 new backend tests (110 total). Verified end-to-end
      against real Postgres and the real seeded government URLs -- the
      scan tolerates real-world flakiness (timeouts, TLS cert errors,
      403s) without aborting. LLM still never decides risk/relevance --
      see rule 4.
- [x] **Phase 4 — Voice/Vernacular + Document AI.** Browser voice input via
      the Web Speech API (`frontend/src/hooks/useSpeechRecognition.ts`) into
      the Compliance Copilot chat, English/Hindi toggle, hidden (not
      disabled) on browsers without support -- frontend-only, no backend
      change. OCR document extraction for 3 document types (GST
      Registration Certificate, Udyam Registration Certificate, PAN Card),
      each mapping onto an existing `Business` column with zero migration:
      `OCRProvider` abstraction (`app/ocr/`) mirroring the LLM/embedding
      pattern exactly, real default is EasyOCR (on-box, no API key,
      `easyocr_provider.py`, downloads a model on first use -- README
      documents a pre-warm step, since a cold first request took ~10
      minutes on this network), `mock` for tests. Field extraction is
      deterministic regex over well-known Indian ID formats
      (`app/ocr/extraction.py`, GSTIN/PAN/Udyam), not LLM-based -- rule 4.
      `POST /documents/extract` takes no DB session and persists nothing;
      the mandatory human-review step is enforced by construction --
      extracted values only land in editable Onboarding form fields and
      are never saved until the user completes the existing submit. Real
      OCR was verified end-to-end against actual synthetic images, not
      just mocks: it correctly recognized text via genuine ML inference,
      and correctly returned a "please verify manually" warning rather
      than silently accepting an OCR misread (0/O confusion) -- the
      human-review design catching exactly the failure mode it exists for.
      20 new backend tests (130 total).
- [x] **Phase 5 — Human-in-the-loop + Submission + Audit.** Real JWT auth
      (`app/core/security.py`: bcrypt + PyJWT, no provider abstraction --
      there's only ever one real implementation, nothing to swap) is
      required only on the new Filing actions (create/approve/reject/
      submit), not retrofitted onto Phases 1-4's routes -- see
      `docs/PROGRESS.md` for the scoping rationale. CA/ADMIN
      form one "reviewer" role via `require_reviewer`
      (`app/api/deps.py`), not a 3-tier permissions framework. Filing
      state machine `DRAFT -> APPROVED|REJECTED -> (if APPROVED) SUBMITTED`
      (`app/services/filings.py`), each transition 409s from the wrong
      starting state; draft documents are deterministic templates, not
      LLM-generated (rule 4); the mock submission notice is a computed
      model property (`Filing.mock`/`mock_notice`) present on every read
      of a SUBMITTED filing, not just the one-time submit response, so
      the "clearly labeled" mock disclosure (rule 5) survives a reload or
      a direct API call. `AuditLog` model + `log_audit_event()`
      (`app/services/audit.py`) wired into Filing's 4 transitions, user
      registration, and a should-have retrofit into Business/Registration
      create+update, Obligation status PATCH, Alert acknowledge, and
      `/compliance/evaluate` -- system-triggered actions (watchdog alerts,
      login attempts) are intentionally not logged, since an audit log's
      value is "which human did what." New migration `0005` (users
      password + audit_logs) plus a same-session bugfix migration `0006`
      (widening `filings.document_ref` VARCHAR(500) -> Text after a real
      Postgres run of the live draft-generation flow hit
      StringDataRightTruncation -- SQLite's lack of VARCHAR enforcement
      let this pass the test suite, caught only by testing against real
      Postgres, same class of bug `0002` fixed for
      `regulations.version`). 22 new backend tests (151 total).
      Login/Filings frontend pages, "Prepare Filing" button on Checklist.
      Verified end-to-end in a real browser: an unauthenticated user is
      redirected to login, an owner cannot approve their own filing (403
      if forced), a CA can approve then submit, and the mock notice
      renders correctly on reload.
- [x] **Phase 6 — Polish + Demo script.** 3 seeded MSME personas
      (`seed/create_demo_personas.py`, idempotent, upserts by name) built
      from the same real service calls the API uses
      (`evaluate_business_compliance`, `generate_growth_forecast_alerts`,
      `create_filing`) rather than fabricated rows -- Ganga Textiles
      Private Limited (18 employees, 2 short of EPF's 20 -> a real
      growth-forecast alert, plus one pre-seeded DRAFT filing ready for
      the demo CA to approve), Coimbatore Micro Traders (clean/compliant
      contrast case), Nilgiri Manufacturing Co. (past EPF+ESI thresholds,
      multiple applicable obligations). Offline fallback is documented
      knobs, not new code -- every provider already defaults to
      something that works with zero network access once its one-time
      setup is done; `WATCHDOG_SCHEDULER_ENABLED=false` avoids repeated
      failing network calls during an offline demo. Containerized
      deployment (Dockerfiles + compose services) intentionally deferred
      under real time pressure ahead of a live demo -- the verified,
      immediately-runnable path is the existing local `uvicorn`/
      `npm run dev` workflow, not a from-scratch Docker build with no
      time left to test it. See the demo pipeline/commands delivered
      directly in-conversation for this phase.

Do not start work on a later phase until the current one is complete and
confirmed — each phase should leave the app in a working, demoable state.

## Conventions

- No comments explaining *what* code does; only *why*, where non-obvious.
- Don't add error handling/fallbacks for scenarios that can't happen in this
  app's actual usage.
- Keep the mock LLM provider's behavior deterministic — tests and demos
  should not depend on real network calls unless `LLM_PROVIDER=anthropic`
  is explicitly set.
