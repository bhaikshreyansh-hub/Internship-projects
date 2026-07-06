"""
FastAPI backend: upload, search, chat, document management.
Updated for Day 2 RAG fixes — uses query decomposition + hybrid search.

Run: uvicorn main:app --reload --port 8000
"""
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ingest_documents import extract_text, clean_text, doc_id_for
from chunk_and_embed import add_document_to_index
from rag_chain import search as rag_search, chat_with_decomposition

UPLOAD_DIR = Path("./raw_documents")
QUERY_LOG = Path("./query_log.jsonl")
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Enterprise Knowledge Base API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_rag_chain = None


def get_chain():
    global _rag_chain
    if _rag_chain is None:
        from rag_chain import build_rag_chain
        _rag_chain = build_rag_chain()
    return _rag_chain


def log_query(query: str, kind: str):
    with QUERY_LOG.open("a") as f:
        f.write(json.dumps({
            "query": query, "kind": kind,
            "ts": datetime.now(timezone.utc).isoformat(),
        }) + "\n")


class SearchRequest(BaseModel):
    query: str
    k: int = 8


class ChatRequest(BaseModel):
    query: str


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    dest = UPLOAD_DIR / file.filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    content = dest.read_bytes()
    text = clean_text(extract_text(str(dest), content))
    if len(text) <= 20:
        raise HTTPException(400, "Could not extract usable text from file")

    did = doc_id_for(str(dest), text)
    try:
        num_chunks = add_document_to_index(did, str(dest), text)
    except Exception as e:
        raise HTTPException(500, f"Saved file but indexing failed: {e}")

    return {
        "filename": file.filename,
        "doc_id": did,
        "preview": text[:200],
        "chunks_indexed": num_chunks,
        "status": "saved and indexed",
    }


@app.post("/search")
async def search_documents(req: SearchRequest):
    log_query(req.query, "search")
    try:
        results = rag_search(req.query, k=req.k)
    except Exception as e:
        raise HTTPException(500, f"Search failed: {e}")
    return {"query": req.query, "results": results}


@app.post("/chat")
async def chat_with_documents(req: ChatRequest):
    log_query(req.query, "chat")
    try:
        chain = get_chain()
        result = chat_with_decomposition(req.query, chain)
    except Exception as e:
        raise HTTPException(500, f"Chat failed: {e}")

    sources = []
    seen = set()
    for d in result.get("source_documents", []):
        src = d.metadata.get("source") or d.metadata.get("filename", "unknown")
        if src not in seen:
            seen.add(src)
            sources.append({
                "source": src,
                "domain": d.metadata.get("domain", ""),
                "doc_id": d.metadata.get("doc_id", ""),
            })

    return {
        "answer": result["result"],
        "sources": sources,
        "decomposed": result.get("decomposed", False),
        "sub_queries": result.get("sub_queries", [req.query]),
    }


@app.get("/documents")
async def list_documents():
    files = sorted(UPLOAD_DIR.glob("*"))
    files = [f for f in files if f.is_file()]
    return {
        "count": len(files),
        "documents": [{"filename": f.name, "size_bytes": f.stat().st_size} for f in files],
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
