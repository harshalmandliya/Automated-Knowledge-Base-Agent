from __future__ import annotations

from sqlalchemy.orm import Session

from backend.services.openai_service import OpenAIService
from backend.vectorstore.faiss_store import FaissStore


class RAGService:
    def __init__(self, db: Session):
        self.db = db
        self.store = FaissStore()
        self.openai_service = OpenAIService()

    def answer(self, question: str, k: int = 4) -> dict:
        contexts = self.store.search(question, k=k)
        if not contexts:
            return {
                "answer": "No indexed source chunks were found. Upload and process documents first.",
                "sources": [],
            }
        answer = self.openai_service.grounded_answer(question, contexts)
        return {"answer": answer, "sources": contexts}

