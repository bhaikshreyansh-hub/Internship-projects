"""
Databricks ingestion job.

Run this as a Databricks notebook/job. It reads raw documents from a Volume
(or S3/DBFS path), extracts + cleans text, and writes a Delta table that acts
as the system of record. Chunking/embedding happens in a separate job
(see chunk_and_embed.py) so re-embedding never requires re-ingesting.

Local fallback: if pyspark isn't available (e.g. running outside Databricks),
falls back to pandas so you can develop against this same script.
"""
import hashlib
import re
from datetime import datetime, timezone

try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import udf, current_timestamp, lit
    from pyspark.sql.types import StringType
    SPARK_AVAILABLE = True
except ImportError:
    SPARK_AVAILABLE = False

RAW_PATH = "/Volumes/main/ekb/raw_documents"          # source files
DELTA_TABLE = "main.ekb.documents"                      # Delta Lake target


def extract_text(path: str, content: bytes) -> str:
    """Extract text depending on file type."""
    if path.lower().endswith(".pdf"):
        from pypdf import PdfReader
        import io
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if path.lower().endswith(".csv"):
        import pandas as pd
        import io
        df = pd.read_csv(io.BytesIO(content))
        return df.to_csv(index=False)
    return content.decode("utf-8", errors="ignore")


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"[^\x20-\x7E\n]", "", text)  # strip non-printable junk
    return text


def doc_id_for(path: str, text: str) -> str:
    return hashlib.sha256((path + text[:200]).encode()).hexdigest()[:16]


def run_spark_job():
    spark = SparkSession.builder.appName("ekb-ingestion").getOrCreate()

    files_df = spark.read.format("binaryFile").load(f"{RAW_PATH}/*")

    extract_udf = udf(lambda path, content: clean_text(extract_text(path, content)), StringType())
    id_udf = udf(doc_id_for, StringType())

    docs_df = (
        files_df
        .withColumn("text", extract_udf("path", "content"))
        .withColumn("doc_id", id_udf("path", "text"))
        .withColumn("ingested_at", current_timestamp())
        .select("doc_id", "path", "text", "ingested_at")
        .dropDuplicates(["doc_id"])
        .filter("length(text) > 20")  # drop empty/garbage extracts
    )

    (docs_df.write
        .format("delta")
        .mode("append")
        .option("mergeSchema", "true")
        .saveAsTable(DELTA_TABLE))

    print(f"Ingested {docs_df.count()} documents into {DELTA_TABLE}")


def run_local_fallback(local_dir: str, out_parquet: str):
    """Dev/test path: same cleaning logic, no Spark/Delta required."""
    import pandas as pd
    from pathlib import Path

    rows = []
    for p in Path(local_dir).glob("*"):
        if not p.is_file():
            continue
        content = p.read_bytes()
        text = clean_text(extract_text(str(p), content))
        if len(text) <= 20:
            continue
        rows.append({
            "doc_id": doc_id_for(str(p), text),
            "path": str(p),
            "text": text,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        })

    df = pd.DataFrame(rows).drop_duplicates(subset=["doc_id"])
    df.to_parquet(out_parquet, index=False)
    print(f"Ingested {len(df)} documents -> {out_parquet}")
    return df


if __name__ == "__main__":
    if SPARK_AVAILABLE:
        run_spark_job()
    else:
        run_local_fallback(local_dir="./raw_documents", out_parquet="./documents.parquet")
