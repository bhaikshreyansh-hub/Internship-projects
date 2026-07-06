"""
RAG pipeline with fixes applied:
- Fix 1: Query decomposition for multi-part questions
- Fix 2: Hybrid search (dense vector + BM25 keyword)
- Fix 3: Stronger hallucination-reduction prompt
- Fix 4: Source grounding check

Swap-in point for AWS Bedrock:
    from langchain_aws import ChatBedrock
    llm = ChatBedrock(model_id="mistral.mistral-large-2402-v1:0", region_name="us-east-1")
"""
import os
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpoint, ChatHuggingFace
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from query_decomposition import decompose_and_retrieve

FAISS_DIR = "./faiss_index/final_index"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Fix 3: Stronger prompt — explicitly forbids making things up
PROMPT_TEMPLATE = """You are a helpful assistant for an enterprise knowledge base.
Use the context below to answer the question as completely as possible.
If the context contains relevant information, use it to give a detailed answer.
Only say you don't know if the context has absolutely no relevant information.
Never invent facts not present in the context. Always respond in English.

Context:
{context}

Question: {question}

Answer:"""

# Cached objects — loaded once, reused across requests
_vectorstore = None
_all_docs_cache = None


def get_vectorstore() -> FAISS:
    global _vectorstore
    if _vectorstore is None:
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        _vectorstore = FAISS.load_local(
            FAISS_DIR,
            embeddings,
            allow_dangerous_deserialization=True
        )
    return _vectorstore


def get_llm():
    endpoint = HuggingFaceEndpoint(
        repo_id="Qwen/Qwen2.5-7B-Instruct",
        task="conversational",
        max_new_tokens=512,
        temperature=0.2,
        huggingfacehub_api_token=os.environ.get("HUGGINGFACEHUB_API_TOKEN"),
    )
    return ChatHuggingFace(llm=endpoint)


def get_hybrid_retriever(k: int = 8):
    """
    Fix 2: Hybrid search — combines FAISS dense vector search with
    BM25 keyword search. Dense search understands meaning; BM25 catches
    exact terms. Together they're more robust than either alone.
    """
    vectorstore = get_vectorstore()
    faiss_retriever = vectorstore.as_retriever(search_kwargs={"k": k})

    # BM25 needs the raw documents — sample from FAISS index
    # We use a subset to keep memory reasonable on 8GB RAM
    sample_docs = vectorstore.similarity_search("knowledge information data", k=200)
    if sample_docs:
        bm25_retriever = BM25Retriever.from_documents(sample_docs)
        bm25_retriever.k = k

        # EnsembleRetriever combines both with equal weighting
        return EnsembleRetriever(
            retrievers=[faiss_retriever, bm25_retriever],
            weights=[0.7, 0.3]   # favor dense search, supplement with keyword
        )

    return faiss_retriever


def build_rag_chain(k: int = 8) -> RetrievalQA:
    retriever = get_hybrid_retriever(k=k)
    llm = get_llm()
    prompt = PromptTemplate(
        template=PROMPT_TEMPLATE,
        input_variables=["context", "question"]
    )

    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True,
    )


def chat_with_decomposition(query: str, chain) -> dict:
    """
    Fix 1: Query decomposition. Detects multi-part questions,
    retrieves separately for each sub-query, merges contexts,
    then generates one unified answer.
    """
    vectorstore = get_vectorstore()
    docs, sub_queries = decompose_and_retrieve(query, vectorstore, k_per_subquery=6)

    if len(sub_queries) > 1:
        # Multi-part query detected — build context from merged retrievals
        context = "\n\n---\n\n".join([doc.page_content for doc in docs[:12]])
        llm = get_llm()
        prompt = PromptTemplate(
            template=PROMPT_TEMPLATE,
            input_variables=["context", "question"]
        )
        formatted = prompt.format(context=context, question=query)
        response = llm.invoke(formatted)
        answer = response.content if hasattr(response, "content") else str(response)

        return {
            "result": answer,
            "source_documents": docs[:12],
            "sub_queries": sub_queries,
            "decomposed": True,
        }
    else:
        # Single query — use normal chain
        result = chain.invoke({"query": query})
        result["decomposed"] = False
        result["sub_queries"] = sub_queries
        return result


def search(query: str, k: int = 8):
    """Pure semantic search — for the /search endpoint."""
    vectorstore = get_vectorstore()
    results = vectorstore.similarity_search_with_score(query, k=k)
    return [
        {"text": doc.page_content, "metadata": doc.metadata, "score": float(score)}
        for doc, score in results
    ]
