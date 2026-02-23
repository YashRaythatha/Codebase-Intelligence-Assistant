"""Run agent (ReAct with tools) first, fallback to RAG; return structured answer with Summary, Evidence, Next steps."""

from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from app.logging_config import get_logger
from app.settings import get_settings
from agent.langchain_tools import build_tools
from agent.memory_store import append_message
from rag.chains import answer_with_rag, parse_structured_answer

logger = get_logger(__name__)

MAX_AGENT_ITERATIONS = 10

AGENT_SYSTEM_WITH_FORMAT = """You are a codebase assistant. Use the tools to explore the repository (list_files, grep, open_file, get_manifest) to find evidence. Answer only using what you discover. Never invent file paths.

When you have enough information, output your final answer in exactly this format:

Summary: (2–4 sentences, direct answer; name key files or functions when relevant)

Evidence: (one citation per line)
FILE: <relative/path> LINES: <start>-<end> (optional brief note)
Only cite files you actually read via open_file or saw in grep/list_files.

Next steps: (2–4 short, actionable bullet-point recommendations relevant to your answer: what to do or explore next—e.g. "• Review X in path/to/file", "• Run tests with pytest". Do not use "Try asking:" or list follow-up questions.)

If you cannot find relevant code, say so in Summary and suggest what to check. Always end with the three sections above."""


def _run_agent_with_tools(
    repo_id: str,
    question: str,
    trace: Any,
    run_id: str,
) -> dict[str, Any]:
    """
    Run ReAct-style agent: LLM + tool-call loop until final answer.
    Returns dict with summary, evidence, next_steps, source="agent" or falls back to RAG on failure.
    """
    settings = get_settings()
    tools = build_tools(repo_id)
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key,
    ).bind_tools(tools)

    name_to_tool = {t.name: t for t in tools}
    messages: list = [
        SystemMessage(content=AGENT_SYSTEM_WITH_FORMAT),
        HumanMessage(content=question),
    ]

    last_response: AIMessage | None = None
    for step in range(MAX_AGENT_ITERATIONS):
        response = llm.invoke(messages)
        last_response = response
        if not getattr(response, "tool_calls", None):
            break
        if trace:
            trace.add_step("agent_tool_calls", {"count": len(response.tool_calls), "names": [getattr(tc, "name", tc.get("name")) for tc in response.tool_calls]})
        tool_messages = []
        for tc in response.tool_calls:
            tid = getattr(tc, "id", None) or (tc.get("id") if isinstance(tc, dict) else None)
            tname = getattr(tc, "name", None) or (tc.get("name") if isinstance(tc, dict) else None)
            targs = getattr(tc, "args", None) or (tc.get("args") if isinstance(tc, dict) else {}) or {}
            if not tname:
                continue
            tool = name_to_tool.get(tname)
            if not tool:
                tool_messages.append(ToolMessage(content=f"Unknown tool: {tname}", tool_call_id=tid or ""))
                continue
            try:
                result = tool.invoke(targs)
                content = result if isinstance(result, str) else str(result)
            except Exception as e:
                logger.warning("Tool %s failed: %s", tname, e)
                content = f"Error: {e}"
            tool_messages.append(ToolMessage(content=content, tool_call_id=tid or ""))
        messages = messages + [response] + tool_messages

    if not last_response or not getattr(last_response, "content", None):
        raise ValueError("Agent produced no final answer")

    raw = last_response.content if isinstance(last_response.content, str) else str(last_response.content)
    try:
        parsed = parse_structured_answer(raw)
        return {
            "summary": parsed.get("summary", raw[:500]),
            "evidence": parsed.get("evidence", []),
            "next_steps": parsed.get("next_steps", ""),
            "source": "agent",
        }
    except Exception as e:
        logger.warning("Agent answer parse failed: %s", e)
        raise


def run_agent(
    repo_id: str,
    conversation_id: str | None,
    question: str,
    trace: Any,
    run_id: str,
) -> dict[str, Any]:
    """
    Run agent (tools) first; on failure or parse error, fall back to RAG.
    Returns dict with summary, evidence[], next_steps, source.
    """
    if conversation_id:
        append_message(repo_id, conversation_id, "user", question)

    try:
        out = _run_agent_with_tools(repo_id, question, trace, run_id)
        if trace:
            trace.add_step("agent_success", {"source": "agent"})
    except Exception as e:
        logger.warning("Agent run failed, falling back to RAG: %s", e)
        if trace:
            trace.add_step("agent_fallback", {"reason": str(e)})
        out = answer_with_rag(repo_id, question)
        out["source"] = "rag"

    evidence = out.get("evidence") or []
    if not evidence and out.get("summary") and out.get("source") == "agent":
        if trace:
            trace.add_step("low_confidence", {"evidence_empty": True})
        try:
            rag_out = answer_with_rag(repo_id, question)
            if rag_out.get("evidence"):
                out = rag_out
                out["source"] = "rag"
                evidence = out.get("evidence", [])
        except Exception:
            pass

    if conversation_id:
        append_message(repo_id, conversation_id, "assistant", out.get("summary", ""))

    return {
        "summary": out.get("summary", ""),
        "evidence": out.get("evidence", []),
        "next_steps": out.get("next_steps", ""),
        "source": out.get("source", "rag"),
    }
