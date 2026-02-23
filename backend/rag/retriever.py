"""Chroma retriever for a repo. Prefers README/docs for overview questions."""

import re
from app.settings import get_settings
import chromadb
from chromadb.utils import embedding_functions
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document


OVERVIEW_PATTERN = re.compile(
    r"\b(what(\s+is|\s+does)?\s+(this\s+)?(project|repo|codebase|app)|"
    r"about\s+this\s+(project|repo)|overview|summary|describe\s+this|"
    r"introduction|what\s+(is|are)\s+it\s+about)\b",
    re.IGNORECASE,
)


def _is_overview_question(query: str) -> bool:
    """True if the question is asking for project/repo overview."""
    return bool(OVERVIEW_PATTERN.search(query.strip()))


def get_retriever(repo_id: str, top_k: int = 10):
    settings = get_settings()
    ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=settings.openai_api_key,
        model_name=settings.openai_embed_model,
    )
    client = chromadb.PersistentClient(path=str(settings.chroma_path))
    collection = client.get_or_create_collection(name=f"repo_{repo_id}", embedding_function=ef)

    class ChromaRetriever(BaseRetriever):
        def _get_relevant_documents(self, query: str, *, run_manager=None):
            doc_chunks: list[Document] = []
            if _is_overview_question(query):
                try:
                    res_doc = collection.query(
                        query_texts=[query],
                        n_results=min(5, top_k),
                        where={"is_doc": True},
                        include=["documents", "metadatas"],
                    )
                    if res_doc.get("documents") and res_doc["documents"][0]:
                        for d, m in zip(
                            res_doc["documents"][0],
                            (res_doc.get("metadatas") or [[]])[0] or [],
                        ):
                            meta = m or {}
                            doc_chunks.append(Document(page_content=d, metadata=meta))
                except Exception:
                    pass

            res = collection.query(
                query_texts=[query],
                n_results=top_k,
                include=["documents", "metadatas"],
            )
            seen = {(doc.metadata.get("path"), doc.metadata.get("start_line")) for doc in doc_chunks}
            for d, m in zip(
                res["documents"][0] if res.get("documents") and res["documents"][0] else [],
                (res.get("metadatas") or [[]])[0] or [],
            ):
                meta = m or {}
                key = (meta.get("path"), meta.get("start_line"))
                if key not in seen:
                    seen.add(key)
                    doc_chunks.append(Document(page_content=d, metadata=meta))
            return doc_chunks[: top_k + 5]

    return ChromaRetriever()
