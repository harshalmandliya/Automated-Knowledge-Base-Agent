from __future__ import annotations

import re
from uuid import uuid4
from pathlib import Path

import pandas as pd
import streamlit as st

from backend.config import settings
from backend.database.session import SessionLocal, init_db
from backend.services.document_service import DocumentService
from backend.services.rag_service import RAGService
from backend.utils.file_utils import ALLOWED_EXTENSIONS

init_db()

st.set_page_config(
    page_title="Automated Knowledge Base Agent",
    page_icon="KB",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main { background: #f6f7fb; }
    .block-container { padding-top: 1.5rem; }
    .kb-card {
        background: white;
        border: 1px solid #e6e8ef;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
    }
    .metric-card {
        background: #111827;
        color: white;
        border-radius: 8px;
        padding: 1rem;
    }
    .tag-pill {
        display: inline-block;
        padding: 0.2rem 0.55rem;
        margin: 0.15rem;
        border-radius: 999px;
        background: #e8f1ff;
        color: #1d4ed8;
        font-size: 0.82rem;
    }
    .source-box {
        border-left: 3px solid #2563eb;
        background: #f8fafc;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_service() -> tuple[SessionLocal, DocumentService]:
    db = SessionLocal()
    return db, DocumentService(db)


if "messages" not in st.session_state:
    st.session_state.messages = []
if "nav" not in st.session_state:
    st.session_state.nav = "Upload"

with st.sidebar:
    st.title("Knowledge Agent")
    st.session_state.nav = st.radio(
        "Navigation",
        ["Upload", "Search / Chat", "Knowledge View", "Analytics"],
        label_visibility="collapsed",
    )

    db, service = get_service()
    try:
        documents = service.list_documents()
    finally:
        db.close()

    st.divider()
    st.subheader("Uploaded Documents")
    if documents:
        for document in documents[:10]:
            st.caption(f"{document['filename']} - {document['chunk_count']} chunks")
    else:
        st.caption("No documents uploaded yet.")

st.title("Automated Knowledge Base Agent")
st.caption("Upload documents, generate summaries and FAQs, then ask grounded questions.")

nav = st.session_state.nav

if nav == "Upload":
    left, right = st.columns([1.2, 0.8])
    with left:
        st.markdown('<div class="kb-card">', unsafe_allow_html=True)
        st.subheader("Upload Documents")
        uploaded_files = st.file_uploader(
            "Drag and drop PDF, DOCX, or TXT files",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
        )
        process = st.button("Process documents", type="primary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if process and uploaded_files:
            progress = st.progress(0)
            for index, uploaded in enumerate(uploaded_files, start=1):
                suffix = Path(uploaded.name).suffix.lower()
                if suffix not in ALLOWED_EXTENSIONS:
                    st.error(f"{uploaded.name}: unsupported file type.")
                    continue
                if uploaded.size > settings.max_upload_mb * 1024 * 1024:
                    st.error(f"{uploaded.name}: file exceeds {settings.max_upload_mb} MB.")
                    continue

                settings.upload_dir.mkdir(parents=True, exist_ok=True)
                doc_id = str(uuid4())
                safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", uploaded.name)
                saved_path = settings.upload_dir / f"{doc_id}_{safe_name}"
                saved_path.write_bytes(uploaded.getbuffer())

                db, service = get_service()
                try:
                    result = service.ingest_saved_file(doc_id, saved_path, suffix, uploaded.name)
                    st.success(f"Processed {result['filename']} with {result['chunks']} chunks.")
                except Exception as exc:
                    st.error(f"{uploaded.name}: {exc}")
                finally:
                    db.close()
                progress.progress(index / len(uploaded_files))
        elif process:
            st.warning("Upload at least one document first.")

    with right:
        st.markdown('<div class="kb-card">', unsafe_allow_html=True)
        st.subheader("Accepted Inputs")
        st.write("PDF, DOCX, and TXT files up to the configured size limit.")
        st.write("Each file is saved locally, parsed, summarized, tagged, chunked, embedded, and indexed.")
        st.markdown("</div>", unsafe_allow_html=True)

elif nav == "Search / Chat":
    st.subheader("Grounded Chat")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    question = st.chat_input("Ask a question about your documents")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        db = SessionLocal()
        try:
            result = RAGService(db).answer(question)
        except Exception as exc:
            result = {"answer": f"Unable to answer: {exc}", "sources": []}
        finally:
            db.close()

        st.session_state.messages.append({"role": "assistant", "content": result["answer"]})
        with st.chat_message("assistant"):
            st.write(result["answer"])
            if result["sources"]:
                st.markdown("**Sources**")
                for source in result["sources"]:
                    st.markdown(
                        f"""
                        <div class="source-box">
                        <strong>{source['filename']}</strong><br/>
                        Chunk: <code>{source['chunk_id']}</code><br/>
                        {source['content'][:500]}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

elif nav == "Knowledge View":
    db, service = get_service()
    try:
        documents = service.list_documents()
    finally:
        db.close()

    st.subheader("Knowledge View")
    if not documents:
        st.info("Upload documents to see summaries, FAQs, tags, and metadata.")
    for document in documents:
        with st.expander(document["filename"], expanded=False):
            meta_a, meta_b, meta_c = st.columns(3)
            meta_a.metric("Chunks", document["chunk_count"])
            meta_b.metric("Type", document["file_type"].replace(".", "").upper())
            meta_c.caption(document["upload_timestamp"])

            st.markdown("**Summary**")
            st.write(document["summary"])

            st.markdown("**Tags**")
            st.markdown(
                " ".join(
                    f"<span class='tag-pill'>{tag['category']}: {tag['name']}</span>"
                    for tag in document["tags"]
                ),
                unsafe_allow_html=True,
            )

            st.markdown("**FAQs**")
            for faq in document["faqs"]:
                st.markdown(f"**{faq['question']}**")
                st.write(faq["answer"])
                st.divider()

elif nav == "Analytics":
    db, service = get_service()
    try:
        analytics = service.analytics()
        documents = service.list_documents()
    finally:
        db.close()

    st.subheader("Analytics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Documents", analytics["total_documents"])
    col2.metric("Total Chunks", analytics["total_chunks"])
    col3.metric("Vector Count", analytics["vector_count"])

    if documents:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "filename": doc["filename"],
                        "type": doc["file_type"],
                        "chunks": doc["chunk_count"],
                        "uploaded": doc["upload_timestamp"],
                    }
                    for doc in documents
                ]
            ),
            use_container_width=True,
        )
