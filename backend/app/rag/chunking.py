from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SectionInput:
    """One structured section of a source document -- e.g. one entry in a
    seed JSON file's `sections` array. Chunking always starts from these
    author-provided boundaries; it does not split raw unstructured text.
    """

    section: str | None
    content: str
    subsection: str | None = None
    source_reference: str | None = None
    source_page: str | None = None


@dataclass(frozen=True)
class ChunkRecord:
    section: str | None
    subsection: str | None
    source_reference: str | None
    source_page: str | None
    content: str
    chunk_index: int
    metadata: dict = field(default_factory=dict)


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def chunk_document(sections: list[SectionInput], max_chars: int = 800) -> list[ChunkRecord]:
    """Deterministic chunking that always respects section boundaries.

    Each `SectionInput` becomes at least one chunk, carrying its
    section/subsection/source_reference/source_page metadata forward
    unchanged. A section is only split further -- on sentence boundaries,
    never mid-sentence -- when its content exceeds `max_chars`, purely to
    keep individual embeddings focused; this is not an arbitrary text
    split, it's a bound on an already-defined section. Same input always
    produces the same output (no randomness, no external calls).
    """
    chunks: list[ChunkRecord] = []
    for section in sections:
        content = section.content.strip()
        if not content:
            continue

        parts = _split_on_sentences(content, max_chars) if len(content) > max_chars else [content]

        for idx, part in enumerate(parts):
            chunks.append(
                ChunkRecord(
                    section=section.section,
                    subsection=section.subsection,
                    source_reference=section.source_reference,
                    source_page=section.source_page,
                    content=part,
                    chunk_index=idx,
                    metadata={"part": idx + 1, "of": len(parts)} if len(parts) > 1 else {},
                )
            )
    return chunks


def _split_on_sentences(text: str, max_chars: int) -> list[str]:
    sentences = _SENTENCE_SPLIT_RE.split(text)
    parts: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) > max_chars and current:
            parts.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        parts.append(current)
    return parts
