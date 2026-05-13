from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.routes.deps import get_db
from backend.services.document_service import DocumentService
from backend.utils.file_utils import save_upload

router = APIRouter()


@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    try:
        doc_id, path, file_type = save_upload(file)
        return DocumentService(db).ingest_saved_file(
            doc_id=doc_id,
            path=path,
            file_type=file_type,
            filename=file.filename or path.name,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

