# Regulatory Document/Chunk Seed Data (Phase 2 demo corpus)

**This is a demo corpus, not an ingested legal corpus.** Every document here
has `"status": "demo"` and `"document_type": "demo_excerpt"`. None of it is
verbatim or independently-sourced statute text -- each `content` field is a
system-authored summary derived directly from the `notes`/`version`/`title`
fields already recorded (and caveated) in `backend/seed/regulations/*.json`
during Phase 1. No new legal claims, section numbers, or thresholds are
introduced here beyond what Phase 1 already verified and disclosed.

## Why this exists

Phase 2 needs a small, retrievable, embedded corpus to prove the RAG
pipeline (chunking → embedding → pgvector retrieval → citation-grounded
answers) end-to-end. We do not have an authoritative ingested legal corpus
(no scraped/OCR'd government PDFs, no verified verbatim statute text) --
inventing one would violate the project's core rule that regulatory
citations must be real. So this seed data is explicitly the honest MVP
state: a demo corpus, clearly labeled, that the Copilot's citation
guardrail treats with the same "requires verification" caution as any
non-`verified` source (see `app/domain/enums.py::SourceStatus`).

## Structure

One JSON file per regulation, `{regulation_code}.json` (lowercase), with:

```json
{
  "code": "unique document code",
  "regulation_code": "must match a code in backend/seed/regulations/",
  "title": "...",
  "authority": "... (same authority as the Phase 1 regulation)",
  "jurisdiction": "IN-Central | IN-STATE",
  "source_url": "... (same verified URL as the Phase 1 regulation)",
  "document_type": "demo_excerpt",
  "effective_date": "YYYY-MM-DD",
  "version": "...",
  "status": "demo",
  "sections": [
    {
      "section": "human-readable section name",
      "subsection": null,
      "source_reference": "citation used in the Phase 1 seed's `version` field, if any",
      "source_page": null,
      "content": "system-authored summary text"
    }
  ]
}
```

`sections` is what `app/rag/chunking.py` chunks (section boundaries are
already given, not inferred). `app/rag/ingestion.py` loads these files,
computes a content hash, embeds each chunk, and upserts
RegulatoryDocument/RegulatoryChunk rows -- see
`backend/seed/load_regulatory_documents.py`.

## Adding real, verified content later

When real authoritative source text becomes available (e.g. a verified
extract from an actual Act, notification, or circular): add a new document
file with `"status": "verified"` and a `document_type` of `act` /
`notification` / `circular` / `faq` as appropriate, with `source_reference`
pointing to the exact section/clause and `source_page` filled in if the
source is a paginated document (PDF). Do not mark anything `verified`
without independently confirming it against the cited `source_url`.
