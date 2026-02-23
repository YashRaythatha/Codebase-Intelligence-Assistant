"""RAG chain: retriever + LLM -> parsed answer."""

import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.settings import get_settings
from rag.prompts import RAG_SYSTEM, RAG_USER_TEMPLATE
from rag.retriever import get_retriever


def _parse_evidence(text: str) -> list[dict]:
    """Extract FILE/LINES (and optional note in parentheses) from model output."""
    evidence = []
    # Match FILE: path LINES: start-end or start–end, with optional (note) after
    for m in re.finditer(
        r"FILE:\s*([^\s\n]+?)\s+LINES:\s*(\d+)\s*[-–]\s*(\d+)\s*(?:\(([^)]*)\))?",
        text,
        re.IGNORECASE,
    ):
        path = m.group(1).strip().rstrip(".,;")
        note = (m.group(4) or "").strip() if m.group(4) else ""
        evidence.append({
            "path": path,
            "start_line": int(m.group(2)),
            "end_line": int(m.group(3)),
            "note": note,
        })
    # Fallback: same pattern without optional note (for backward compatibility)
    if not evidence:
        for m in re.finditer(r"FILE:\s*([^\s\n]+)\s+LINES:\s*(\d+)\s*[-–]?\s*(\d+)", text, re.IGNORECASE):
            path = m.group(1).strip().rstrip(".,;")
            evidence.append({
                "path": path,
                "start_line": int(m.group(2)),
                "end_line": int(m.group(3)),
                "note": "",
            })
    return evidence


def parse_structured_answer(raw: str) -> dict:
    """
    Parse LLM raw text into summary, evidence list, next_steps.
    Used by both RAG chain and agent. Returns dict with keys: summary, evidence, next_steps.
    """
    summary = ""
    evidence_text = ""
    next_steps = ""
    ev_match = re.search(r"\bEvidence:\s*", raw, re.IGNORECASE)
    ns_match = re.search(r"\bNext steps:\s*", raw, re.IGNORECASE)
    ev_pos = ev_match.start() if ev_match else -1
    ns_pos = ns_match.start() if ns_match else -1

    if "Summary:" in raw:
        after_summary = raw.split("Summary:", 1)[1]
        if ev_pos >= 0 and "Evidence:" in after_summary:
            summary = after_summary.split("Evidence:", 1)[0].strip()
        elif ns_pos >= 0 and "Next steps:" in after_summary:
            summary = after_summary.split("Next steps:", 1)[0].strip()
        else:
            summary = after_summary.strip()
        if "Next steps:" in summary:
            summary = summary.split("Next steps:", 1)[0].strip()
    else:
        summary = raw[:500].strip()

    if ev_pos >= 0:
        start = ev_match.end()  # type: ignore[union-attr]
        if ns_pos > ev_pos:
            evidence_text = raw[start:ns_pos].strip()
        else:
            evidence_text = raw[start:].strip()
        if "Next steps:" in evidence_text:
            evidence_text = evidence_text.split("Next steps:", 1)[0].strip()
    evidence = _parse_evidence(evidence_text if evidence_text else raw)

    if ns_pos >= 0:
        next_steps = raw[ns_match.end():].strip()  # type: ignore[union-attr]
    if not next_steps or not next_steps.replace("-", "").strip():
        next_steps = "• Check the README or docs for how to run the project.\n• Look at the main entry points or API routes.\n• Review package.json or requirements for dependencies."

    return {
        "summary": summary or raw[:500],
        "evidence": evidence,
        "next_steps": next_steps,
    }


def answer_with_rag(repo_id: str, question: str) -> dict:
    """Run RAG: retrieve chunks, call LLM, parse Summary / Evidence / Next steps."""
    settings = get_settings()
    retriever = get_retriever(repo_id)
    docs = retriever.invoke(question)
    context = "\n\n---\n\n".join(d.page_content for d in docs)

    prompt = ChatPromptTemplate.from_messages([
        ("system", RAG_SYSTEM),
        ("human", RAG_USER_TEMPLATE),
    ])
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key,
    )
    chain = prompt | llm | StrOutputParser()
    raw = chain.invoke({"context": context, "question": question})
    parsed = parse_structured_answer(raw)
    return {**parsed, "source": "rag"}
