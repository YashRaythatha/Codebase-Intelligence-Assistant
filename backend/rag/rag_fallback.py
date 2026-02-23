"""RAG fallback: run_rag(repo_id, question, trace, run_id) -> structured answer with summary, evidence[], next_steps[]."""

from typing import Any

from rag.chains import answer_with_rag


def run_rag(
    repo_id: str,
    question: str,
    trace: Any,
    run_id: str,
) -> dict:
    """
    Run RAG: retrieve, prompt, parse. Record retrieval and token usage in trace.
    Returns dict: summary, evidence[], next_steps (string).
    """
    if trace:
        trace.add_step("rag_retrieval", {"query": question[:200]})
    out = answer_with_rag(repo_id, question)
    if trace:
        trace.add_step("rag_answer", {"summary_preview": (out.get("summary") or "")[:200], "evidence_count": len(out.get("evidence") or [])})
    return {
        "summary": out.get("summary", ""),
        "evidence": out.get("evidence", []),
        "next_steps": out.get("next_steps", ""),
        "source": "rag",
    }
