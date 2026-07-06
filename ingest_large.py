"""
Large Scale Ingestion + Embedding (Memory Safe)
=================================================
Designed for machines with ~8GB RAM. Processes documents in small
batches so memory never spikes, and saves progress after each batch
so it's safe to interrupt and restart.

Uses FAISS instead of ChromaDB for better performance at scale.

Run from project root (venv activated):
    pip install faiss-cpu langchain-community
    python ingest_large.py

Estimated time: 4-8 hours depending on machine speed.
Safe to Ctrl+C and restart — progress is saved after each batch.
"""

import os
import json
import pickle
import hashlib
import re
from pathlib import Path
from datetime import datetime

DATASET_DIR = Path("./raw_documents/large_dataset")
FAISS_DIR = Path("./faiss_index")
PROGRESS_FILE = Path("./ingest_progress.json")
BATCH_SIZE = 500        # chunks per batch — safe for 8GB RAM
CHUNK_SIZE = 800        # characters per chunk
CHUNK_OVERLAP = 150     # overlap between chunks
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

FAISS_DIR.mkdir(exist_ok=True)


def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"processed_files": [], "total_chunks": 0}


def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


def doc_id_for(path: str, text: str) -> str:
    return hashlib.sha256((path + text[:200]).encode()).hexdigest()[:16]


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"[^\x20-\x7E\n]", "", text)
    return text


def chunk_text(text: str, chunk_size: int, overlap: int):
    """Split text into overlapping chunks, preferring paragraph boundaries."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            # try to break at paragraph boundary
            para_break = text.rfind("\n\n", start, end)
            if para_break > start + chunk_size // 2:
                end = para_break
            else:
                # fall back to sentence boundary
                sent_break = text.rfind(". ", start, end)
                if sent_break > start + chunk_size // 2:
                    end = sent_break + 1
        chunks.append(text[start:end].strip())
        start = end - overlap
    return [c for c in chunks if len(c) > 50]


def get_all_files():
    """Get all .txt files from the large dataset directory."""
    return sorted(DATASET_DIR.rglob("*.txt"))


def embed_and_save_batch(texts, metadatas, batch_num, embeddings_model):
    """Embed a batch of chunks and save to disk."""
    from langchain_community.vectorstores import FAISS

    print(f"    Embedding {len(texts)} chunks...")
    batch_index_path = FAISS_DIR / f"batch_{batch_num:04d}"

    if batch_index_path.exists():
        print(f"    Batch {batch_num} already exists, skipping.")
        return

    vectordb = FAISS.from_texts(
        texts=texts,
        embedding=embeddings_model,
        metadatas=metadatas,
    )
    vectordb.save_local(str(batch_index_path))
    print(f"    Saved batch {batch_num} -> {batch_index_path}")


def merge_faiss_indexes():
    """Merge all batch FAISS indexes into one final index."""
    from langchain_community.vectorstores import FAISS
    from langchain_huggingface import HuggingFaceEmbeddings

    print("\nMerging all batch indexes into final FAISS index...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    batch_dirs = sorted(FAISS_DIR.glob("batch_*"))
    if not batch_dirs:
        print("No batch indexes found!")
        return

    print(f"Found {len(batch_dirs)} batches to merge.")
    merged = FAISS.load_local(str(batch_dirs[0]), embeddings,
                              allow_dangerous_deserialization=True)

    for batch_dir in batch_dirs[1:]:
        print(f"  Merging {batch_dir.name}...")
        batch = FAISS.load_local(str(batch_dir), embeddings,
                                 allow_dangerous_deserialization=True)
        merged.merge_from(batch)

    final_path = FAISS_DIR / "final_index"
    merged.save_local(str(final_path))
    print(f"Final index saved -> {final_path}")
    return merged


def main():
    from langchain_huggingface import HuggingFaceEmbeddings

    print("Large Scale Ingestion + Embedding")
    print(f"Dataset: {DATASET_DIR}")
    print(f"Chunk size: {CHUNK_SIZE} chars, overlap: {CHUNK_OVERLAP}")
    print(f"Batch size: {BATCH_SIZE} chunks\n")

    # Load progress
    progress = load_progress()
    processed_files = set(progress["processed_files"])
    total_chunks_so_far = progress["total_chunks"]

    # Get all files
    all_files = get_all_files()
    remaining = [f for f in all_files if str(f) not in processed_files]

    print(f"Total files found : {len(all_files)}")
    print(f"Already processed : {len(processed_files)}")
    print(f"Remaining         : {len(remaining)}\n")

    if not remaining:
        print("All files already processed. Running merge step...")
        merge_faiss_indexes()
        return

    # Load embedding model once
    print("Loading embedding model (one-time download if first run)...")
    embeddings_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    print("Embedding model loaded.\n")

    # Determine next batch number
    existing_batches = list(FAISS_DIR.glob("batch_*"))
    batch_num = len(existing_batches)

    # Process files in batches
    current_texts = []
    current_metadatas = []
    file_count = 0
    total_chunks = total_chunks_so_far

    for file_path in remaining:
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            text = clean_text(text)
            if len(text) < 100:
                continue

            did = doc_id_for(str(file_path), text)
            chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
            domain = file_path.parent.name
            fname = file_path.name

            for i, chunk in enumerate(chunks):
                current_texts.append(chunk)
                current_metadatas.append({
                    "doc_id": did,
                    "source": str(file_path),
                    "filename": fname,
                    "domain": domain,
                    "chunk_index": i,
                })

            processed_files.add(str(file_path))
            file_count += 1
            total_chunks += len(chunks)

            # Embed and save when batch is full
            if len(current_texts) >= BATCH_SIZE:
                print(f"\nBatch {batch_num} | Files processed: {file_count} | "
                      f"Chunks so far: {total_chunks}")
                embed_and_save_batch(current_texts, current_metadatas,
                                     batch_num, embeddings_model)
                batch_num += 1
                current_texts = []
                current_metadatas = []

                # Save progress
                progress["processed_files"] = list(processed_files)
                progress["total_chunks"] = total_chunks
                save_progress(progress)
                print(f"Progress saved. Safe to Ctrl+C here if needed.")

        except Exception as e:
            print(f"  ERROR processing {file_path.name}: {e}")
            continue

    # Embed any remaining chunks
    if current_texts:
        print(f"\nFinal batch {batch_num} | {len(current_texts)} remaining chunks")
        embed_and_save_batch(current_texts, current_metadatas,
                             batch_num, embeddings_model)
        progress["processed_files"] = list(processed_files)
        progress["total_chunks"] = total_chunks
        save_progress(progress)

    print(f"\n{'='*55}")
    print(f"Ingestion complete.")
    print(f"Total files processed : {len(processed_files)}")
    print(f"Total chunks embedded : {total_chunks}")
    print(f"\nNow merging batch indexes...")
    merge_faiss_indexes()
    print(f"\nDone. Run the app and test queries.")


if __name__ == "__main__":
    main()
