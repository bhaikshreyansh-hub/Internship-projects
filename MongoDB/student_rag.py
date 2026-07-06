from pymongo import MongoClient
import chromadb
from sentence_transformers import SentenceTransformer
from transformers import pipeline

uri = "mongodb+srv://bhaikshreyansh_db_user:Shreyansh%4004@cluster0.rmspwfd.mongodb.net/?appName=Cluster0"
client = MongoClient(uri)
db = client["college"]
students_collection = db["students"]

print("Fetching students from MongoDB...")
students = list(students_collection.find({}, {"_id": 0}))
print(f"Fetched {len(students)} students")

def student_to_text(s):
    return (
        f"Student ID: {s['student_id']}. "
        f"Name: {s['name']}. "
        f"Age: {s['age']}. "
        f"Gender: {s['gender']}. "
        f"Course: {s['course']}. "
        f"Semester: {s['semester']}. "
        f"CGPA: {s['cgpa']}. "
        f"Subjects: {', '.join(s['subjects'])}. "
        f"Skills: {', '.join(s['skills'])}. "
        f"City: {s['address']['city']}, {s['address']['state']}."
    )

documents = [student_to_text(s) for s in students]
ids = [str(s["student_id"]) for s in students]

print("\nLoading embedding model...")
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="students")

# Embed in batches of 50 to avoid memory issues
print("Embedding and storing students in ChromaDB...")
batch_size = 50
for i in range(0, len(documents), batch_size):
    batch_docs = documents[i:i + batch_size]
    batch_ids = ids[i:i + batch_size]
    batch_embeddings = embed_model.encode(batch_docs).tolist()
    collection.add(
        documents=batch_docs,
        embeddings=batch_embeddings,
        ids=batch_ids
    )
    print(f"  Stored {min(i + batch_size, len(documents))}/{len(documents)} students...")

print(f"\nAll {collection.count()} students stored in vector DB!")


print("\nLoading Flan-T5 model (downloads once ~900MB)...")
generator = pipeline("text-generation", model="google/flan-t5-base")

def retrieve(query, top_k=5):
    query_embedding = embed_model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )
    return results["documents"][0]

def generate_answer(query, context_docs):
    context = " ".join(context_docs)
    prompt = f"Context: {context}\n\nQuestion: {query}\nAnswer:"
    result = generator(prompt, max_new_tokens=150)
    return result[0]["generated_text"]

def rag(query):
    print(f"\nQuestion: {query}")
    relevant_docs = retrieve(query)
    print(f"Retrieved {len(relevant_docs)} relevant student records")
    answer = generate_answer(query, relevant_docs)
    print(f"Answer: {answer}")
    return answer

rag("Which students are studying Artificial Intelligence?")
rag("List students who know Python and have high CGPA above 9.")
rag("Which students are from Mumbai?")
rag("Who are the students in semester 1?")
rag("Which students have Machine Learning as a subject?")
