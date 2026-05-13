from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.routes.deps import get_db
from backend.services.rag_service import RAGService

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    k: int = 4


@router.post("/query")
def query(request: QueryRequest, db: Session = Depends(get_db)) -> dict:
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question is required.")
    try:
        return RAGService(db).answer(request.question, k=request.k)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

