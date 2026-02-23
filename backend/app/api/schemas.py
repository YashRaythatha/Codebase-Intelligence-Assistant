"""Pydantic schemas for API request/response."""

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    """Request to index a repo from URL or local path."""

    source: str | None = None
    repo_url: str | None = None
    local_path: str | None = None
    branch: str | None = None


class IngestResponse(BaseModel):
    """Result of ingest: repo_id and optional framework detection."""

    repo_id: str
    index_stats: dict | None = None
    detected: dict | None = None


class AskRequest(BaseModel):
    """Request to ask a question about an indexed repo."""

    repo_id: str = Field(..., min_length=1, description="ID of the indexed repository")
    conversation_id: str | None = None
    question: str = Field(..., min_length=1, max_length=8000, description="Question about the codebase")
    use_agent: bool = True


class EvidenceItem(BaseModel):
    """A single file/line citation."""

    path: str
    start_line: int
    end_line: int
    note: str | None = None


class AnswerBody(BaseModel):
    """Structured answer: summary, evidence list, next steps (actionable recommendations)."""

    summary: str
    evidence: list[EvidenceItem] = []
    next_steps: list[str] | None = None


class AskResponse(BaseModel):
    """Full ask response with answer body and trace_id."""

    answer: AnswerBody
    trace_id: str


class FileLine(BaseModel):
    """A single line with 1-based line number."""

    no: int
    text: str


class FileResponse(BaseModel):
    """File content or snippet (path, optional range, lines)."""

    file: str
    start: int | None = None
    end: int | None = None
    lines: list[FileLine]
