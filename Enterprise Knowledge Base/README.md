# Enterprise Knowledge Base — Starter Scaffold

## What's here
```
ingestion/
  ingest_documents.py   # Databricks Spark job (Delta Lake) + local fallback
  chunk_and_embed.py    # chunking + embedding -> ChromaDB
backend/
  rag_chain.py           # LangChain retriever + Mistral LLM
  main.py                 # FastAPI: /upload /search /chat /documents
frontend/
  streamlit_app.py        # upload, search, chat, dashboard UI
requirements.txt
```

## Local run (no AWS/Databricks needed yet)
```bash
pip install -r requirements.txt --break-system-packages

# 1. put some PDFs/CSVs/TXT files in ./raw_documents, then:
python ingestion/ingest_documents.py        # -> documents.parquet
python ingestion/chunk_and_embed.py          # -> chroma_db/

# 2. start the API
export HUGGINGFACEHUB_API_TOKEN=...          # needed for Mistral generation
cd backend && uvicorn main:app --reload --port 8000

# 3. start the UI (separate terminal)
cd frontend && streamlit run streamlit_app.py
```

## Where this maps to your mentor's stack, and what changes for AWS deployment

| Stage | Now (dev) | Production (per spec) |
|---|---|---|
| Ingestion | pandas fallback in `ingest_documents.py` | Same script's Spark/Delta path runs as-is on Databricks — just point `RAW_PATH` at a Volume/S3 path and schedule as a job |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (local, free) | Swap to Bedrock Titan embeddings in `chunk_and_embed.py` — one function change |
| Vector DB | ChromaDB, local persist dir | Same Chroma client pointed at a persistent volume/EBS, or swap to FAISS if scale demands it — `rag_chain.py`'s retriever interface barely changes |
| LLM | Mistral-7B via HF Inference endpoint | Swap `get_llm()` to `ChatBedrock` with a Mistral model id (commented inline in `rag_chain.py`) |
| Backend | FastAPI on localhost | Same app, containerize + deploy on ECS/Fargate or EC2 behind ALB |
| Frontend | Streamlit | Keep Streamlit, or port to React hitting the same FastAPI endpoints unchanged |

## Known gaps to flag to your mentor (intentional, for scoping discussion)
- `/upload` lands the file but doesn't auto-trigger re-indexing — needs a Databricks Jobs API call or a watch-folder trigger.
- No auth/access control yet — needed before this touches real company documents.
- No document deletion/versioning in the vector store.
- Dashboard's cluster visualization needs an `/embeddings` endpoint (noted in the UI as a next step).
