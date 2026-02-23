"""Legacy entry: delegate to agent.agent_runner (agent-first then RAG fallback)."""

from agent.agent_runner import run_agent
from rag.chains import answer_with_rag


def invoke_agent(repo_id: str, question: str, conversation_id: str | None = None, trace=None, run_id: str | None = None) -> dict:
    """Legacy: run agent then RAG fallback. Returns summary, evidence, next_steps, source."""
    if run_id and trace is not None:
        return run_agent(repo_id, conversation_id, question, trace, run_id)
    result = run_agent(repo_id, conversation_id, question, None, run_id or "legacy")
    return result
