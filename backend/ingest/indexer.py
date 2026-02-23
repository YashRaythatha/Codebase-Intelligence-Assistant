"""Index chunks into Chroma and write manifest."""

import json
from pathlib import Path

from app.logging_config import get_logger
from app.settings import get_settings

from ingest.loader import load_repo
from ingest.scanner import scan_files, is_doc_path
from ingest.chunker import chunk_file

logger = get_logger(__name__)


def index_repo(source: str) -> str:
    """Load repo, scan, chunk, embed, index. Return repo_id."""
    import chromadb
    from chromadb.utils import embedding_functions

    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required for indexing")

    repo_id, repo_root = load_repo(source)
    repos_base = settings.repos_path
    manifest_dir = repos_base / repo_id
    manifest_dir.mkdir(parents=True, exist_ok=True)

    files = scan_files(repo_root)
    all_chunks: list[dict] = []
    for rel in files:
        for c in chunk_file(repo_root, rel):
            c["repo_id"] = repo_id
            all_chunks.append(c)

    manifest = {
        "repo_id": repo_id,
        "source": source,
        "repo_root": str(repo_root),
        "files": [str(f).replace("\\", "/") for f in files],
    }
    (manifest_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    if not all_chunks:
        return repo_id

    ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=settings.openai_api_key,
        model_name=settings.openai_embed_model,
    )
    client = chromadb.PersistentClient(path=str(settings.chroma_path))
    collection = client.get_or_create_collection(name=f"repo_{repo_id}", embedding_function=ef)

    ids = [f"{repo_id}_{i}" for i in range(len(all_chunks))]
    documents = [c["text"] for c in all_chunks]
    metadatas = [
        {
            "path": c["path"],
            "start_line": c["start_line"],
            "end_line": c["end_line"],
            "is_doc": is_doc_path(Path(c["path"])),
        }
        for c in all_chunks
    ]

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    logger.info("Indexed repo_id=%s chunks=%d", repo_id, len(all_chunks))
    return repo_id
