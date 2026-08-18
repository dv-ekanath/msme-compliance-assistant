# Regulatory Knowledge Base — Seed Data

This directory holds the source-of-truth regulation entries that will be
loaded into Postgres (`regulation` + `regulation_chunk` tables) once the
Digital Twin models exist (Phase 1) and the RAG pipeline is built (Phase 2).

**Phase 0 only defines the structure.** No regulation content is loaded yet
— there is no loader script and no domain tables to load it into.

## Structure

- `schema.json` — JSON Schema every seed entry must satisfy.
- `_template.sample.json` — a placeholder entry showing the shape. It is
  **not verified legal content** — do not use it as a real citation source.
- One JSON file per regulation, named `<code>.json` (e.g.
  `gst-registration-threshold.json`), added as the corpus is curated.

## Rules for real entries (when added in Phase 1/2)

1. `source_url` must point to an actual government source (e.g.
   `gst.gov.in`, `udyamregistration.gov.in`, `epfindia.gov.in`,
   `esic.gov.in`, a state Shops & Establishment Act page).
2. `chunks[].text` must be traceable back to that source — this corpus is
   what the LLM reasoning layer is required to cite, so accuracy here
   directly determines whether the app's citations are trustworthy.
3. `applicability_rules` must be concrete and machine-checkable (numeric
   thresholds, enums) so Phase 1's deterministic Rules Engine can evaluate
   them without an LLM in the loop.
