from __future__ import annotations

from app.rag.chunking import SectionInput, chunk_document


def test_each_section_becomes_at_least_one_chunk():
    sections = [
        SectionInput(section="A", content="Short content A."),
        SectionInput(section="B", content="Short content B."),
    ]
    chunks = chunk_document(sections)
    assert len(chunks) == 2
    assert {c.section for c in chunks} == {"A", "B"}


def test_section_metadata_is_preserved():
    sections = [
        SectionInput(
            section="Registration Threshold",
            subsection="Goods",
            source_reference="CGST Act 2017, Section 22",
            source_page="12",
            content="Businesses must register once turnover crosses the threshold.",
        )
    ]
    chunks = chunk_document(sections)
    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.section == "Registration Threshold"
    assert chunk.subsection == "Goods"
    assert chunk.source_reference == "CGST Act 2017, Section 22"
    assert chunk.source_page == "12"
    assert "threshold" in chunk.content


def test_short_section_is_not_split():
    sections = [SectionInput(section="A", content="One short sentence.")]
    chunks = chunk_document(sections, max_chars=800)
    assert len(chunks) == 1
    assert chunks[0].metadata == {}


def test_long_section_is_split_on_sentence_boundaries_not_arbitrarily():
    long_content = " ".join(f"This is sentence number {i} of a very long section." for i in range(1, 30))
    sections = [SectionInput(section="Long Section", content=long_content)]
    chunks = chunk_document(sections, max_chars=200)

    assert len(chunks) > 1
    # every chunk still carries the parent section's metadata
    assert all(c.section == "Long Section" for c in chunks)
    # split points are sentence boundaries: every chunk ends with punctuation
    assert all(c.content.rstrip()[-1] in ".!?" for c in chunks)
    # chunk_index is stable/ordered
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
    # reassembling the chunks recovers the original text losslessly
    assert " ".join(c.content for c in chunks) == long_content


def test_chunking_is_deterministic():
    sections = [SectionInput(section="A", content="Some content. " * 50)]
    first = chunk_document(sections, max_chars=300)
    second = chunk_document(sections, max_chars=300)
    assert first == second


def test_empty_section_content_is_skipped():
    sections = [
        SectionInput(section="Empty", content="   "),
        SectionInput(section="Real", content="Actual content here."),
    ]
    chunks = chunk_document(sections)
    assert len(chunks) == 1
    assert chunks[0].section == "Real"
