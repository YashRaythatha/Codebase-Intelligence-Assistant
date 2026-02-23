"""Ensure prompt layer constants exist (PROMPT 7)."""

from rag import prompts


def test_agent_system_prompt_exists():
    assert hasattr(prompts, "AGENT_SYSTEM_PROMPT")
    assert isinstance(prompts.AGENT_SYSTEM_PROMPT, str)
    assert "Summary" in prompts.AGENT_SYSTEM_PROMPT
    assert "Evidence" in prompts.AGENT_SYSTEM_PROMPT
    assert "Next Steps" in prompts.AGENT_SYSTEM_PROMPT


def test_rag_answer_prompt_exists():
    assert hasattr(prompts, "RAG_ANSWER_PROMPT")
    assert isinstance(prompts.RAG_ANSWER_PROMPT, str)


def test_tool_extraction_prompts_exist():
    assert hasattr(prompts, "TOOL_EXTRACTION_ENDPOINT")
    assert hasattr(prompts, "TOOL_EXTRACTION_AUTH")
    assert isinstance(prompts.TOOL_EXTRACTION_ENDPOINT, str)
    assert isinstance(prompts.TOOL_EXTRACTION_AUTH, str)
