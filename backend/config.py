from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
import os

ROOT_DIR = Path(__file__).resolve().parents[1]

load_dotenv(ROOT_DIR / ".env")
load_dotenv(ROOT_DIR / "backend" / ".env", override=False)
load_dotenv(ROOT_DIR / ".env.example", override=False)


def _secret(name: str) -> str:
    value = os.getenv(name, "").strip()
    if value in {"", "your_openai_api_key"}:
        return ""
    return value


class Settings:
    app_name = "Automated Knowledge Base Agent"
    openai_api_key = _secret("OPENAI_API_KEY")
    chat_model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    database_url = os.getenv("DATABASE_URL", f"sqlite:///{ROOT_DIR / 'backend' / 'knowledge_base.db'}")
    upload_dir = Path(os.getenv("UPLOAD_DIR", ROOT_DIR / "backend" / "uploads"))
    faiss_dir = Path(os.getenv("FAISS_DIR", ROOT_DIR / "backend" / "vectorstore" / "faiss_index"))
    max_upload_mb = int(os.getenv("MAX_UPLOAD_MB", "15"))
    chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "150"))


settings = Settings()
