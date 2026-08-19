from __future__ import annotations

from app.llm.base import LLMMessage
from app.rag.retrieval import RetrievedChunk

SYSTEM_PROMPT = """You are the Compliance Copilot for an MSME Compliance Assistant.

Ground rules (do not break these):
1. You are an EXPLANATION layer, not a legal authority. The deterministic Rules Engine, not you, decides whether an obligation applies to a business -- never re-derive or override that decision.
2. Use ONLY the numbered evidence items in EVIDENCE below for any legal claim (law name, section, threshold, deadline, penalty, government URL, or which states/categories something applies to). Never invent, guess, or generalize beyond what an evidence item literally states -- if the evidence doesn't name a specific state or list, do not claim one.
3. MANDATORY CITATION FORMAT: every sentence containing a legal claim MUST end with a citation tag in the exact form [S1], [S2], etc., referencing the evidence item number. Example: "The threshold is Rs 40 lakh for goods suppliers [S1]." A response with zero [Sn] tags is treated as unusable by this system, so include at least one even in a short answer.
4. If the evidence does not sufficiently answer the question, say so explicitly and recommend the user verify with the cited source(s) or a professional -- do not fill the gap from your own general knowledge.
5. Never claim legal certainty. Every evidence item is demo or otherwise unreviewed content pending full legal verification, so always note that verification is required before acting on it.
6. You may use BUSINESS CONTEXT to personalize the explanation (e.g. "because your business has 45 employees...").
7. Keep the answer concise (a few sentences or a short list) -- this is a compliance summary, not an essay.
"""


def build_evidence_block(retrieved: list[RetrievedChunk]) -> str:
    if not retrieved:
        return "(no relevant regulatory evidence was retrieved for this question)"
    lines = []
    for idx, chunk in enumerate(retrieved, start=1):
        section = f", Section: {chunk.section}" if chunk.section else ""
        ref = f" ({chunk.source_reference})" if chunk.source_reference else ""
        lines.append(
            f'[S{idx}] {chunk.title} — {chunk.authority}{section}{ref} [status: {chunk.status}]\n'
            f'"{chunk.content}"\n(source: {chunk.source_url})'
        )
    return "\n\n".join(lines)


def build_copilot_messages(
    *, question: str, twin_context: str, retrieved: list[RetrievedChunk]
) -> list[LLMMessage]:
    user_content = (
        f"BUSINESS CONTEXT:\n{twin_context}\n\n"
        f"EVIDENCE:\n{build_evidence_block(retrieved)}\n\n"
        f"QUESTION: {question}\n\n"
        f"Reminder: cite each evidence-based claim as [S1], [S2], etc. Do not name any state, "
        f"category, or threshold that is not explicitly written in the evidence above."
    )
    return [
        LLMMessage(role="system", content=SYSTEM_PROMPT),
        LLMMessage(role="user", content=user_content),
    ]
