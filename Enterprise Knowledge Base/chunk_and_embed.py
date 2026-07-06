"""
Chunk + embed job. Reads cleaned documents (Delta table in prod, parquet in
dev) and writes vectors to ChromaDB. Kept separate from ingestion so you can
re-chunk or swap embedding models without re-processing raw files.

Swap-in point for AWS: replace HuggingFaceEmbeddings with Bedrock Titan
embeddings (bedrock-runtime + amazon.titan-embed-text-v2) once deployed.
"""
import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

CHROMA_DIR = "./chroma_db"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # swap for Bedrock Titan in prod


def load_documents(parquet_path: str = "./documents.parquet") -> pd.DataFrame:
    # In prod: spark.table("main.ekb.documents").toPandas() (batched, not all at once)
    return pd.read_parquet(parquet_path)


def chunk_and_embed(parquet_path: str = "./documents.parquet"):
    df = load_documents(parquet_path)
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

    texts, metadatas, ids = [], [], []
    for _, row in df.iterrows():
        chunks = splitter.split_text(row["text"])
        for i, chunk in enumerate(chunks):
            texts.append(chunk)
            metadatas.append({"doc_id": row["doc_id"], "source": row["path"], "chunk_index": i})
            ids.append(f"{row['doc_id']}_{i}")

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectordb = Chroma.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas,
        ids=ids,
        persist_directory=CHROMA_DIR,
    )
    print(f"Embedded {len(texts)} chunks from {len(df)} documents -> {CHROMA_DIR}")
    return vectordb


def add_document_to_index(doc_id: str, path: str, text: str):
    """
    Incrementally embed a single document and add it to the existing Chroma
    index, without re-processing every previously indexed document. Used by
    the /upload endpoint so new files become searchable immediately.
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(text)
    if not chunks:
        return 0

    metadatas = [{"doc_id": doc_id, "source": path, "chunk_index": i} for i in range(len(chunks))]
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectordb = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
    vectordb.add_texts(texts=chunks, metadatas=metadatas, ids=ids)
    return len(chunks)


if __name__ == "__main__":
    chunk_and_embed()
