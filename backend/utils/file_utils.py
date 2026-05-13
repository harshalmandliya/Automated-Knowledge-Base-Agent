from __future__ import annotations

import re
import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

from backend.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def validate_upload(file: UploadFile) -> str:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise ValueError(f"Unsupported file type. Allowed types: {allowed}")
    return suffix


def save_upload(file: UploadFile) -> tuple[str, Path, str]:
    suffix = validate_upload(file)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    doc_id = str(uuid.uuid4())
    safe_name = _safe_filename(file.filename or f"document{suffix}")
    target = settings.upload_dir / f"{doc_id}_{safe_name}"

    bytes_written = 0
    max_bytes = settings.max_upload_mb * 1024 * 1024
    with target.open("wb") as output:
        while chunk := file.file.read(1024 * 1024):
            bytes_written += len(chunk)
            if bytes_written > max_bytes:
                target.unlink(missing_ok=True)
                raise ValueError(f"File exceeds {settings.max_upload_mb} MB limit")
            output.write(chunk)

    file.file.seek(0)
    return doc_id, target, suffix


def copy_local_document(path: Path) -> tuple[str, Path, str]:
    suffix = path.suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {suffix}")
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    doc_id = str(uuid.uuid4())
    target = settings.upload_dir / f"{doc_id}_{_safe_filename(path.name)}"
    shutil.copy2(path, target)
    return doc_id, target, suffix


def _safe_filename(filename: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", filename)

