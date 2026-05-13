from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.database.session import SessionLocal, init_db
from backend.services.rag_service import RAGService


def evaluate(dataset_path: Path) -> dict:
    init_db()
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    db = SessionLocal()
    rows = []
    try:
        rag = RAGService(db)
        for item in dataset:
            result = rag.answer(item["question"], k=4)
            sources = result.get("sources", [])
            retrieved_files = {source["filename"] for source in sources}
            answer = result.get("answer", "").lower()
            required_terms = [term.lower() for term in item.get("required_terms", [])]
            source_hit = item["expected_source"] in retrieved_files
            term_hit = all(term in answer for term in required_terms)
            rows.append(
                {
                    "question": item["question"],
                    "expected_source": item["expected_source"],
                    "retrieved_files": sorted(retrieved_files),
                    "source_hit": source_hit,
                    "answer_contains_required_terms": term_hit,
                }
            )
    finally:
        db.close()

    total = len(rows)
    return {
        "retrieval_hit_rate": sum(row["source_hit"] for row in rows) / total if total else 0,
        "answer_quality_rate": sum(row["answer_contains_required_terms"] for row in rows) / total
        if total
        else 0,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate RAG retrieval and answer quality.")
    parser.add_argument("--dataset", default="eval/sample_rag_dataset.json")
    args = parser.parse_args()
    print(json.dumps(evaluate(Path(args.dataset)), indent=2))


if __name__ == "__main__":
    main()
