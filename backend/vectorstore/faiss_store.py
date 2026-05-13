from __future__ import annotations

from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document as LCDocument
from langchain_openai import OpenAIEmbeddings

from backend.config import settings


class FaissStore:
    def __init__(self) -> None:
        self.index_path = Path(settings.faiss_dir)

    def add_chunks(self, chunks: list[dict]) -> None:
        if not chunks:
            return
        embeddings = self._embeddings()
        docs = [
            LCDocument(
                page_content=chunk["content"],
                metadata={
                    "doc_id": chunk["doc_id"],
                    "chunk_id": chunk["chunk_id"],
                    "filename": chunk["filename"],
                },
            )
            for chunk in chunks
        ]

        if self._exists():
            store = FAISS.load_local(
                str(self.index_path),
                embeddings,
                allow_dangerous_deserialization=True,
            )
            store.add_documents(docs)
        else:
            self.index_path.mkdir(parents=True, exist_ok=True)
            store = FAISS.from_documents(docs, embeddings)
        store.save_local(str(self.index_path))

    def search(self, query: str, k: int = 4) -> list[dict]:
        if not self._exists():
            return []
        embeddings = self._embeddings()
        store = FAISS.load_local(
            str(self.index_path),
            embeddings,
            allow_dangerous_deserialization=True,
        )
        results = store.similarity_search_with_score(query, k=k)
        return [
            {
                "content": doc.page_content,
                "score": float(score),
                "doc_id": doc.metadata.get("doc_id", ""),
                "chunk_id": doc.metadata.get("chunk_id", ""),
                "filename": doc.metadata.get("filename", ""),
            }
            for doc, score in results
        ]

    def vector_count(self) -> int:
        if not self._exists():
            return 0
        embeddings = self._embeddings()
        store = FAISS.load_local(
            str(self.index_path),
            embeddings,
            allow_dangerous_deserialization=True,
        )
        return store.index.ntotal

    def _exists(self) -> bool:
        return (self.index_path / "index.faiss").exists()

    def _embeddings(self) -> OpenAIEmbeddings:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is missing. Add it to .env.")
        return OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key,
        )
