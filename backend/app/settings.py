"""App settings from environment."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _repo_root() -> Path:
    """Project root (parent of backend when run from repo or /app in Docker)."""
    p = Path(__file__).resolve().parent.parent.parent
    return p


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_repo_root() / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_embed_model: str = "text-embedding-3-small"

    chroma_dir: str = "./data/indexes"
    log_dir: str = "./data/logs"
    trace_dir: str = "./data/traces"
    repos_base: str = "./data/repos"
    allowed_origins: str = "http://localhost:3000"

    # Alias for REPO_DIR (prompt compatibility)
    repo_dir: str | None = None

    log_level: str = "INFO"

    @property
    def chroma_path(self) -> Path:
        root = _repo_root()
        return (root / self.chroma_dir).resolve()

    @property
    def trace_path(self) -> Path:
        root = _repo_root()
        return (root / self.trace_dir).resolve()

    @property
    def log_path(self) -> Path:
        root = _repo_root()
        return (root / self.log_dir).resolve()

    @property
    def repos_path(self) -> Path:
        root = _repo_root()
        base = self.repo_dir or self.repos_base
        return (root / base).resolve()

    def ensure_dirs(self) -> None:
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        self.trace_path.mkdir(parents=True, exist_ok=True)
        self.log_path.mkdir(parents=True, exist_ok=True)
        self.repos_path.mkdir(parents=True, exist_ok=True)


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
