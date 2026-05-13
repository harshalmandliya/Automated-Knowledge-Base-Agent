from pathlib import Path

from backend.utils.document_parser import extract_text
from backend.utils.text import clean_text, split_text


def test_txt_parser_extracts_sample_text() -> None:
    text = extract_text(Path("sample_docs/security.txt"))

    assert "multi-factor authentication" in text
    assert "manager-approved recovery code" in text


def test_clean_and_split_text_returns_chunks() -> None:
    raw = "Title\r\n\r\nA useful sentence about policy. " * 40
    chunks = split_text(clean_text(raw))

    assert chunks
    assert all(chunk.strip() for chunk in chunks)
