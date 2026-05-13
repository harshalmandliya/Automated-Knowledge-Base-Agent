from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from backend.database.models import Chunk, Document, FAQ, Summary, Tag
from backend.services.openai_service import OpenAIService
from backend.utils.document_parser import extract_text
from backend.utils.file_utils import copy_local_document
from backend.utils.logger import get_logger
from backend.utils.text import clean_text, split_text
from backend.vectorstore.faiss_store import FaissStore

logger = get_logger(__name__)


class DocumentService:
    def __init__(self, db: Session):
        self.db = db

    def ingest_saved_file(self, doc_id: str, path: Path, file_type: str, filename: str) -> dict:
        text = clean_text(extract_text(path))
        if not text:
            raise ValueError("No text could be extracted from the document.")

        chunks = split_text(text)
        openai_service = OpenAIService()
        summary = openai_service.summarize(text)
        faqs = openai_service.generate_faqs(text)
        tags = openai_service.generate_tags(text)

        document = Document(
            id=doc_id,
            filename=filename,
            file_path=str(path),
            file_type=file_type,
            extracted_content=text,
            chunk_count=len(chunks),
        )
        self.db.add(document)
        self.db.flush()
        self.db.add(Summary(doc_id=doc_id, content=summary))

        for item in faqs:
            self.db.add(
                FAQ(
                    doc_id=doc_id,
                    question=str(item.get("question", "")).strip(),
                    answer=str(item.get("answer", "")).strip(),
                    source_quote=str(item.get("source_quote", "")).strip(),
                )
            )

        for item in tags:
            self.db.add(
                Tag(
                    doc_id=doc_id,
                    name=str(item.get("name", "")).strip().lower(),
                    category=str(item.get("category", "general")).strip().lower(),
                )
            )

        vector_chunks = []
        for index, content in enumerate(chunks):
            chunk_id = f"{doc_id}-{index}"
            self.db.add(Chunk(id=chunk_id, doc_id=doc_id, chunk_index=index, content=content))
            vector_chunks.append(
                {
                    "doc_id": doc_id,
                    "chunk_id": chunk_id,
                    "filename": filename,
                    "content": content,
                }
            )

        self.db.commit()
        FaissStore().add_chunks(vector_chunks)
        logger.info("Ingested %s with %s chunks", filename, len(chunks))
        return {"doc_id": doc_id, "filename": filename, "chunks": len(chunks)}

    def ingest_local_path(self, path: Path) -> dict:
        doc_id, saved_path, file_type = copy_local_document(path)
        return self.ingest_saved_file(doc_id, saved_path, file_type, path.name)

    def list_documents(self) -> list[dict]:
        documents = self.db.query(Document).order_by(Document.upload_timestamp.desc()).all()
        return [serialize_document(document, include_content=False) for document in documents]

    def get_summary(self, doc_id: str) -> dict | None:
        summary = self.db.query(Summary).filter(Summary.doc_id == doc_id).first()
        return {"doc_id": doc_id, "summary": summary.content} if summary else None

    def get_faqs(self, doc_id: str) -> list[dict]:
        faqs = self.db.query(FAQ).filter(FAQ.doc_id == doc_id).all()
        return [
            {
                "question": faq.question,
                "answer": faq.answer,
                "source_quote": faq.source_quote,
            }
            for faq in faqs
        ]

    def analytics(self) -> dict:
        return {
            "total_documents": self.db.query(Document).count(),
            "total_chunks": self.db.query(Chunk).count(),
            "vector_count": FaissStore().vector_count(),
        }


def serialize_document(document: Document, include_content: bool = True) -> dict:
    payload = {
        "id": document.id,
        "filename": document.filename,
        "file_type": document.file_type,
        "upload_timestamp": document.upload_timestamp.isoformat(),
        "chunk_count": document.chunk_count,
        "summary": document.summary.content if document.summary else "",
        "tags": [
            {"name": tag.name, "category": tag.category}
            for tag in document.tags
            if tag.name
        ],
        "faqs": [
            {
                "question": faq.question,
                "answer": faq.answer,
                "source_quote": faq.source_quote,
            }
            for faq in document.faqs
            if faq.question and faq.answer
        ],
    }
    if include_content:
        payload["extracted_content"] = document.extracted_content
    return payload

