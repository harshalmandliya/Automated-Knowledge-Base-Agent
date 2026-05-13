# Automated Knowledge Base Agent

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-red)

A full-stack AI knowledge-base system built with OpenAI, LangChain, FAISS, SQLite, FastAPI, and Streamlit.

The app ingests PDF, DOCX, and TXT files, extracts text, generates summaries, FAQs, tags, semantic embeddings, and answers user questions with Retrieval-Augmented Generation (RAG).

## Features

- PDF, DOCX, and TXT upload
- Local file storage with validation and file-size checks
- OpenAI-powered summarization, FAQ generation, and tagging
- LangChain text splitting
- OpenAI embeddings with `text-embedding-3-small`
- FAISS semantic vector search
- RAG answers with `gpt-4o-mini`
- SQLite metadata storage
- Streamlit dashboard with upload, chat, knowledge view, and analytics
- FastAPI backend with REST endpoints
- Evaluation dataset and retrieval/answer quality script
- Logging, reusable services, and modular code

## Architecture Flow

```text
Upload File
   |
   v
Text Extraction
   |
   v
Chunking (LangChain)
   |
   v
OpenAI Embeddings
   |
   v
FAISS Vector Store
   |
   v
RAG Retrieval
   |
   v
GPT-4o-mini Answer Generation
```

## Project Structure

```text
backend/
  main.py
  routes/
  services/
  database/
  vectorstore/
  utils/
  uploads/
  requirements.txt
.env
app.py
requirements.txt
scripts/
eval/
sample_docs/
tests/
explanation.md
```

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## OpenAI API Setup

Create or update `.env` in the project root:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
DATABASE_URL=sqlite:///backend/knowledge_base.db
UPLOAD_DIR=backend/uploads
FAISS_DIR=backend/vectorstore/faiss_index
MAX_UPLOAD_MB=15
CHUNK_SIZE=1000
CHUNK_OVERLAP=150
```


## Run The FastAPI Backend

```powershell
.\.venv\Scripts\uvicorn.exe backend.main:app --reload
```

Open API docs:

```text
http://127.0.0.1:8000/docs
```

## Run The Streamlit Frontend

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

Streamlit usually opens:

```text
http://localhost:8501
```

## Ingest Sample Documents

The sample folder includes TXT files that can be indexed from the command line:

```powershell
.\.venv\Scripts\python.exe scripts\ingest.py --docs sample_docs
```

You can also upload PDF, DOCX, or TXT files from the Streamlit dashboard.

## API Endpoints

### Health

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

### Upload Document

```http
POST /upload
```

Multipart form field:

```text
file=@policy.pdf
```

Sample response:

```json
{
  "doc_id": "91fd5b92-4e49-42c6-a947-559b85592af7",
  "filename": "policy.pdf",
  "chunks": 8
}
```

### Query

```http
POST /query
```

Request:

```json
{
  "question": "How does an employee recover MFA access?",
  "k": 4
}
```

Response:

```json
{
  "answer": "Employees should contact the service desk and verify their identity with a manager-approved recovery code [chunk-id].",
  "sources": [
    {
      "content": "Employees must use multi-factor authentication...",
      "score": 0.28,
      "doc_id": "91fd5b92-4e49-42c6-a947-559b85592af7",
      "chunk_id": "91fd5b92-4e49-42c6-a947-559b85592af7-0",
      "filename": "security.txt"
    }
  ]
}
```

### Documents

```http
GET /documents
```

### Analytics

```http
GET /analytics
```

Response includes total documents, total chunks, and the current FAISS vector count.

### Summary

```http
GET /summary/{doc_id}
```

### FAQs

```http
GET /faqs/{doc_id}
```

## SQLite Tables

The backend creates:

- `documents`
- `summaries`
- `faqs`
- `tags`
- `chunks`

Stored metadata includes filename, upload timestamp, extracted content, generated summary, generated FAQ pairs, tags/categories, and chunk records.

## Local Runtime Artifacts

The app creates local state while you use it:

- uploaded files in `backend/uploads`
- SQLite database at `backend/knowledge_base.db`
- FAISS index files in `backend/vectorstore/faiss_index`
- Python caches such as `__pycache__`


## Evaluation

Run retrieval and answer quality checks:

```powershell
.\.venv\Scripts\python.exe scripts\evaluate.py --dataset eval\sample_rag_dataset.json
```

The script reports:

- retrieval hit rate
- answer quality rate based on required terms
- per-question retrieved sources


## Troubleshooting

`OPENAI_API_KEY is missing`

Add your key to `.env`, then restart Streamlit or FastAPI.

`No indexed source chunks were found`

Upload and process at least one document, or run:

```powershell
.\.venv\Scripts\python.exe scripts\ingest.py --docs sample_docs
```

`FAISS index not found`

This is normal before the first successful ingestion. The index is created at `backend/vectorstore/faiss_index`.

`Unsupported file type`

Only `.pdf`, `.docx`, and `.txt` files are accepted.

`File exceeds size limit`

Increase `MAX_UPLOAD_MB` in `.env` if needed.

## Development Checks

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m py_compile app.py backend\main.py
```

## License

MIT License
