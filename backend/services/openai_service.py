from __future__ import annotations

import json

from openai import OpenAI

from backend.config import settings


class OpenAIService:
    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is missing. Add it to .env.")
        self.client = OpenAI(api_key=settings.openai_api_key)

    def summarize(self, text: str) -> str:
        response = self.client.chat.completions.create(
            model=settings.chat_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You generate concise knowledge-base summaries. Use only "
                        "facts from the source. Write 3-5 clear sentences."
                    ),
                },
                {"role": "user", "content": text[:12000]},
            ],
            temperature=0.1,
        )
        return (response.choices[0].message.content or "").strip()

    def generate_faqs(self, text: str) -> list[dict]:
        response = self.client.chat.completions.create(
            model=settings.chat_model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Generate useful FAQ pairs from the source. Return JSON with "
                        "`faqs`, an array of objects containing question, answer, and "
                        "source_quote. Answers must be factual and grounded."
                    ),
                },
                {"role": "user", "content": text[:12000]},
            ],
            temperature=0.2,
        )
        payload = json.loads(response.choices[0].message.content or "{}")
        return payload.get("faqs", [])[:10]

    def generate_tags(self, text: str) -> list[dict]:
        response = self.client.chat.completions.create(
            model=settings.chat_model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract taxonomy tags for a knowledge base. Return JSON with "
                        "`tags`, an array of objects containing name and category. "
                        "Prefer short business-friendly labels."
                    ),
                },
                {"role": "user", "content": text[:9000]},
            ],
            temperature=0.1,
        )
        payload = json.loads(response.choices[0].message.content or "{}")
        return payload.get("tags", [])[:12]

    def grounded_answer(self, question: str, contexts: list[dict]) -> str:
        context_text = "\n\n".join(
            f"[{item['chunk_id']}] {item['filename']}\n{item['content']}"
            for item in contexts
        )
        response = self.client.chat.completions.create(
            model=settings.chat_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Answer using only the supplied context. Be concise and factual. "
                        "Cite chunk IDs inline like [chunk_id]. If the context does not "
                        "contain the answer, say you do not have enough information."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Question: {question}\n\nContext:\n{context_text}",
                },
            ],
            temperature=0.1,
        )
        return (response.choices[0].message.content or "").strip()

