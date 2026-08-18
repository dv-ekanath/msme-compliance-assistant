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

1. **LLM provider abstraction is mandatory.** No application code outside
   `backend/app/llm/` may import the `anthropic` SDK or any other vendor
   LLM SDK directly. All LLM calls go through `app.llm.factory.get_llm_provider()`
   returning an `LLMProvider` (`backend/app/llm/base.py`). The default
   provider is `mock` (`LLM_PROVIDER=mock` in `backend/.env`) — the app must
   run fully without an Anthropic API key. Do not assume the developer's
   Claude Pro subscription provides API credits for this app.
2. **Don't introduce infra that isn't earning its place.** No Neo4j, no
   LangChain/LangGraph, no Redis/Celery, no separate vector DB — pgvector
   inside the existing Postgres, and a plain relational model for the
   knowledge graph, are sufficient at this project's scale. Revisit only if
   a concrete need appears.
3. **Real corpus, real citations.** Regulation seed data
   (`backend/seed/regulations/`) must trace back to genuine government
   sources (gst.gov.in, udyamregistration.gov.in, epfindia.gov.in,
   esic.gov.in, state Shops & Establishment Act pages, etc.) with an actual
   `source_url`. Never fabricate regulation text or citations, even as
   placeholder/demo content — mark placeholders explicitly as templates
   (see `_template.sample.json`).
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
- Embeddings (Phase 2+): local sentence-transformers, no external API needed
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
- [ ] **Phase 2 — RAG + Explainability.** Curate real regulation corpus,
      embed via pgvector, retrieval + citation-grounded chat endpoint (must
      use the `LLMProvider` abstraction), chat UI, KG-linked "why this
      obligation" explanations.
- [ ] **Phase 3 — Predictive + Watchdog.** Heuristic risk scoring/forecast
      (explainable, not ML), scheduled watchdog scan job, KG-based
      affected-business matching, alerts UI.
- [ ] **Phase 4 — Voice/Vernacular + Document AI.** Browser voice input
      (Web Speech API) into the chat pipeline, Hindi + English, OCR
      extraction for 2–3 document types with a mandatory human review step.
- [ ] **Phase 5 — Human-in-the-loop + Submission + Audit.** Approval queue,
      mock submission draft generation (clearly labeled as mock), audit log
      wired across all state-changing actions.
- [ ] **Phase 6 — Polish + Demo script.** Seeded MSME personas, scripted
      live demo flow, deployment, offline fallback.

Do not start work on a later phase until the current one is complete and
confirmed — each phase should leave the app in a working, demoable state.

## Conventions

- No comments explaining *what* code does; only *why*, where non-obvious.
- Don't add error handling/fallbacks for scenarios that can't happen in this
  app's actual usage.
- Keep the mock LLM provider's behavior deterministic — tests and demos
  should not depend on real network calls unless `LLM_PROVIDER=anthropic`
  is explicitly set.
