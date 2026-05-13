from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.routes.deps import get_db
from backend.services.document_service import DocumentService

router = APIRouter()


@router.get("/documents")
def documents(db: Session = Depends(get_db)) -> list[dict]:
    return DocumentService(db).list_documents()


@router.get("/summary/{doc_id}")
def summary(doc_id: str, db: Session = Depends(get_db)) -> dict:
    result = DocumentService(db).get_summary(doc_id)
    if not result:
        raise HTTPException(status_code=404, detail="Summary not found.")
    return result


@router.get("/faqs/{doc_id}")
def faqs(doc_id: str, db: Session = Depends(get_db)) -> list[dict]:
    return DocumentService(db).get_faqs(doc_id)


@router.get("/analytics")
def analytics(db: Session = Depends(get_db)) -> dict:
    return DocumentService(db).analytics()

