"""LangChain tools for the ReAct agent: list_files, grep, open_file, get_manifest (bound to repo_id)."""

import json
from typing import Annotated

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from agent import tools as agent_tools


def build_tools(repo_id: str) -> list:
    """Build a list of LangChain tools bound to this repo_id for the agent."""

    class ListFilesInput(BaseModel):
        pattern: Annotated[str, Field(description="Glob pattern to filter paths, e.g. '*.py' or '*' for all")] = "*"

    class GrepInput(BaseModel):
        pattern: Annotated[str, Field(description="Regex pattern to search for in file contents")]
        glob: Annotated[str, Field(description="Glob to limit files, e.g. '**/*.py'")] = "**/*"

    class OpenFileInput(BaseModel):
        rel_path: Annotated[str, Field(description="Relative path to file from repo root")]
        start: Annotated[int | None, Field(description="Start line (1-based), optional")] = None
        end: Annotated[int | None, Field(description="End line (1-based), optional")] = None

    class GetManifestInput(BaseModel):
        pass  # No args

    def run_list_files(pattern: str = "*") -> str:
        paths = agent_tools.list_files(repo_id, pattern)
        return json.dumps(paths[:100], indent=0) if paths else "[]"

    def run_grep(pattern: str, glob: str = "**/*") -> str:
        matches = agent_tools.grep(repo_id, pattern, glob)
        return json.dumps(matches[:50], indent=0) if matches else "[]"

    def run_open_file(rel_path: str, start: int | None = None, end: int | None = None) -> str:
        lines = agent_tools.open_file(repo_id, rel_path, start, end, max_lines=150)
        if not lines:
            return "File not found or path invalid."
        return json.dumps(lines, indent=0)

    def run_get_manifest() -> str:
        out = agent_tools.get_manifest(repo_id)
        return json.dumps(out, indent=0)

    tools_list = [
        StructuredTool(
            name="list_files",
            description="List file paths in the repository. Use pattern '*' for all, or e.g. '*.py' for Python files.",
            args_schema=ListFilesInput,
            func=lambda pattern="*": run_list_files(pattern),
        ),
        StructuredTool(
            name="grep",
            description="Search for a regex pattern in repository files. Returns matching file, line number, and line text.",
            args_schema=GrepInput,
            func=lambda pattern="", glob="**/*": run_grep(pattern, glob),
        ),
        StructuredTool(
            name="open_file",
            description="Read a file by relative path. Optionally give start and end line (1-based) for a snippet.",
            args_schema=OpenFileInput,
            func=lambda rel_path="", start=None, end=None: run_open_file(rel_path, start, end),
        ),
        StructuredTool(
            name="get_manifest",
            description="Get repo manifest summary: repo_id, repo_root, file count.",
            args_schema=GetManifestInput,
            func=run_get_manifest,
        ),
    ]
    return tools_list
