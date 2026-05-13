from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.database.session import SessionLocal, init_db
from backend.services.document_service import DocumentService


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest all supported docs from a folder.")
    parser.add_argument("--docs", default="sample_docs")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        service = DocumentService(db)
        for path in Path(args.docs).rglob("*"):
            if path.suffix.lower() in {".pdf", ".docx", ".txt"}:
                result = service.ingest_local_path(path)
                print(f"Indexed {result['filename']} with {result['chunks']} chunks.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
