"""
LLM Model Comparison for RAG Pipeline
======================================
Runs the same test queries through multiple HF-hosted models using the
same ChromaDB retriever, records answers + response times, and writes a
CSV report you can share with your mentor.

Run from the project root (with venv activated):
    python model_compare.py

Output: model_comparison_results.csv
"""
import os
import time
import csv
from datetime import datetime

from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpoint, ChatHuggingFace
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# ── Config ────────────────────────────────────────────────────────────────────

CHROMA_DIR = "./chroma_db"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
HF_TOKEN = os.environ.get("HUGGINGFACEHUB_API_TOKEN")

MODELS = [
    {
        "name": "Qwen2.5-7B-Instruct",
        "repo_id": "Qwen/Qwen2.5-7B-Instruct",
    },
    {
        "name": "Qwen2.5-3B-Instruct",
        "repo_id": "Qwen/Qwen2.5-3B-Instruct",
    },
    {
        "name": "Qwen2.5-1.5B-Instruct",
        "repo_id": "Qwen/Qwen2.5-1.5B-Instruct",
    },
    {
        "name": "Qwen2.5-0.5B-Instruct",
        "repo_id": "Qwen/Qwen2.5-0.5B-Instruct",
    },
]

# Queries strictly matching documents confirmed indexed in ChromaDB
TEST_QUERIES = [
    {
        "query": "How many sick days do employees get per year?",
        "expected_keyword": "10",
        "source_doc": "leave_policy.txt",
    },
    {
        "query": "What should I do if I click a phishing link?",
        "expected_keyword": "disconnect",
        "source_doc": "it_security_guidelines.txt",
    },
    {
        "query": "How do I export my data before closing my account?",
        "expected_keyword": "export",
        "source_doc": "customer_support_faq.txt",
    },
    {
        "query": "What is metallurgy?",
        "expected_keyword": "metal",
        "source_doc": "metallurgy.pdf",
    },
    {
        "query": "What are the steps to isolate metals from ores?",
        "expected_keyword": "concentration",
        "source_doc": "metallurgy.pdf",
    },
]

PROMPT_TEMPLATE = """You are an assistant answering questions using only the provided context
from the organization's knowledge base. If the answer isn't in the context, say you don't know
rather than guessing. Do not mention "the context" or cite sources in your answer.
Always respond in English.

Context:
{context}

Question: {question}

Answer (in English):"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_retriever():
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectordb = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
    return vectordb.as_retriever(search_kwargs={"k": 4})


def build_chain(repo_id: str, retriever):
    endpoint = HuggingFaceEndpoint(
        repo_id=repo_id,
        task="conversational",
        max_new_tokens=512,
        temperature=0.2,
        huggingfacehub_api_token=HF_TOKEN,
    )
    llm = ChatHuggingFace(llm=endpoint)
    prompt = PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["context", "question"])
    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True,
    )


def check_accuracy(answer: str, expected_keyword: str) -> str:
    """Simple keyword-based accuracy check — not a perfect metric but gives
    a consistent, repeatable signal across models for comparison purposes."""
    if expected_keyword.lower() in answer.lower():
        return "PASS"
    return "FAIL"


def sources_from_result(result) -> str:
    seen = set()
    sources = []
    for doc in result.get("source_documents", []):
        src = doc.metadata.get("source", "unknown")
        if src not in seen:
            seen.add(src)
            sources.append(src.split("\\")[-1].split("/")[-1])  # filename only
    return ", ".join(sources)


# ── Main ──────────────────────────────────────────────────────────────────────

def run_comparison():
    if not HF_TOKEN:
        print("ERROR: HUGGINGFACEHUB_API_TOKEN not set. Run: set HUGGINGFACEHUB_API_TOKEN=...")
        return

    print("Loading retriever...")
    retriever = get_retriever()

    results = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    for model in MODELS:
        print(f"\n{'='*60}")
        print(f"Testing model: {model['name']}")
        print(f"{'='*60}")

        try:
            chain = build_chain(model["repo_id"], retriever)
        except Exception as e:
            print(f"  Failed to load model: {e}")
            for q in TEST_QUERIES:
                results.append({
                    "timestamp": timestamp,
                    "model": model["name"],
                    "query": q["query"],
                    "answer": f"MODEL LOAD ERROR: {e}",
                    "accuracy": "ERROR",
                    "response_time_sec": "-",
                    "sources_retrieved": "-",
                    "expected_source": q["source_doc"],
                })
            continue

        for q in TEST_QUERIES:
            print(f"\n  Query: {q['query']}")
            try:
                start = time.time()
                result = chain.invoke({"query": q["query"]})
                elapsed = round(time.time() - start, 2)
                answer = result["result"].strip()
                accuracy = check_accuracy(answer, q["expected_keyword"])
                sources = sources_from_result(result)
            except Exception as e:
                answer = f"ERROR: {e}"
                elapsed = "-"
                accuracy = "ERROR"
                sources = "-"

            print(f"  Answer: {answer[:120]}{'...' if len(answer) > 120 else ''}")
            print(f"  Accuracy: {accuracy} | Time: {elapsed}s | Sources: {sources}")

            results.append({
                "timestamp": timestamp,
                "model": model["name"],
                "query": q["query"],
                "answer": answer,
                "accuracy": accuracy,
                "response_time_sec": elapsed,
                "sources_retrieved": sources,
                "expected_source": q["source_doc"],
            })

    # Write CSV
    out_file = "model_comparison_results.csv"
    fieldnames = ["timestamp", "model", "query", "answer", "accuracy",
                  "response_time_sec", "sources_retrieved", "expected_source"]
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n{'='*60}")
    print(f"Results saved to {out_file}")

    # Print summary table
    print(f"\n{'Model':<30} {'Accuracy':<12} {'Avg Time (s)':<15}")
    print("-" * 57)
    for model in MODELS:
        model_rows = [r for r in results if r["model"] == model["name"]]
        passes = sum(1 for r in model_rows if r["accuracy"] == "PASS")
        total = len(model_rows)
        times = [r["response_time_sec"] for r in model_rows if isinstance(r["response_time_sec"], float)]
        avg_time = round(sum(times) / len(times), 2) if times else "-"
        print(f"{model['name']:<30} {passes}/{total} PASS    {avg_time}")


if __name__ == "__main__":
    run_comparison()
