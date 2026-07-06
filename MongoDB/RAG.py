import chromadb
from sentence_transformers import SentenceTransformer
from transformers import pipeline

documents = [
    "RAG stands for Retrieval Augmented Generation.",
    "ChromaDB is an open-source vector database for AI applications.",
    "Embeddings convert text into numerical vectors that capture meaning.",
    "Vector databases store embeddings and allow similarity search.",
    "sentence-transformers is a Python library to create text embeddings.",
    "Cosine similarity measures how similar two vectors are.",
    "In RAG, relevant documents are retrieved and given to an LLM as context.",
    "OpenAI GPT models can generate human-like text responses."
]

ids = [f"doc{i}" for i in range(len(documents))]

embed_model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.Client()
collection = client.create_collection(name="rag_knowledge_base")

embeddings = embed_model.encode(documents).tolist()
collection.add(documents=documents, embeddings=embeddings, ids=ids)
print(f"Stored {collection.count()} documents in vector DB")

generator = pipeline("text-generation", model="google/flan-t5-base")

def retrieve(query, top_k=3):
    query_embedding = embed_model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=top_k)
    return results["documents"][0]

def generate_answer(query, context_docs):
    context = " ".join(context_docs)
    prompt = f"Context: {context}\n\nQuestion: {query}\nAnswer:"
    result = generator(prompt, max_new_tokens=100)
    return result[0]["generated_text"]

def rag(query):
    print(f"\nQuestion: {query}")
    relevant_docs = retrieve(query)
    print(f"Retrieved {len(relevant_docs)} relevant docs")
    answer = generate_answer(query, relevant_docs)
    print(f"Answer: {answer}")
    return answer

rag("What is RAG and how does it work?")
rag("What library do I use to create embeddings?")
rag("What is ChromaDB used for?")