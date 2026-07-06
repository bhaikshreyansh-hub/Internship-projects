"""
Streamlit frontend. Run: streamlit run streamlit_app.py
Talks to the FastAPI backend over HTTP — keeps frontend/backend decoupled so
you can swap in React later without touching the API.
"""
import json
from pathlib import Path
from collections import Counter

import requests
import streamlit as st
import pandas as pd
import plotly.express as px

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Enterprise Knowledge Base", layout="wide")
st.title("📚 Enterprise Knowledge Base")

tab_upload, tab_search, tab_chat, tab_dashboard = st.tabs(
    ["Upload", "Search", "Chat", "Dashboard"]
)

with tab_upload:
    st.subheader("Upload a document")
    uploaded = st.file_uploader("PDF, CSV, or TXT", type=["pdf", "csv", "txt"])
    if uploaded and st.button("Upload"):
        resp = requests.post(
            f"{API_URL}/upload",
            files={"file": (uploaded.name, uploaded.getvalue())},
        )
        if resp.ok:
            data = resp.json()
            st.success(f"Uploaded and indexed {data['chunks_indexed']} chunks from {data['filename']} — ready to search/chat now.")
        else:
            st.error(resp.text)

    st.subheader("Indexed documents")
    docs_resp = requests.get(f"{API_URL}/documents")
    if docs_resp.ok:
        docs = docs_resp.json()
        st.write(f"{docs['count']} documents")
        st.dataframe(pd.DataFrame(docs["documents"]))

with tab_search:
    st.subheader("Semantic search")
    query = st.text_input("Search query", key="search_q")
    k = st.slider("Number of results", 1, 10, 5)
    if st.button("Search") and query:
        resp = requests.post(f"{API_URL}/search", json={"query": query, "k": k})
        if resp.ok:
            for r in resp.json()["results"]:
                with st.expander(f"score={r['score']:.3f} — {r['metadata'].get('source', 'unknown')}"):
                    st.write(r["text"])
        else:
            st.error(resp.text)

with tab_chat:
    st.subheader("Chat with your documents")
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_msg = st.chat_input("Ask a question about your documents")
    if user_msg:
        st.session_state.messages.append({"role": "user", "content": user_msg})
        with st.chat_message("user"):
            st.write(user_msg)

        resp = requests.post(f"{API_URL}/chat", json={"query": user_msg})
        with st.chat_message("assistant"):
            if resp.ok:
                data = resp.json()
                st.write(data["answer"])
                if data["sources"]:
                    st.caption("Sources: " + ", ".join(s["source"] or "?" for s in data["sources"]))
                st.session_state.messages.append({"role": "assistant", "content": data["answer"]})
            else:
                st.error(resp.text)

with tab_dashboard:
    st.subheader("Insights")
    docs_resp = requests.get(f"{API_URL}/documents")
    if docs_resp.ok:
        st.metric("Total documents indexed", docs_resp.json()["count"])

    # Search trend log (written by the backend on every /search and /chat call)
    log_path = Path("./query_log.jsonl")
    if log_path.exists():
        rows = [json.loads(line) for line in log_path.read_text().splitlines() if line.strip()]
        if rows:
            df = pd.DataFrame(rows)
            df["ts"] = pd.to_datetime(df["ts"], format="ISO8601")
            df["date"] = df["ts"].dt.strftime("%Y-%m-%d")
            trend = df.groupby(["date", "kind"]).size().reset_index(name="count")
            st.plotly_chart(px.bar(trend, x="date", y="count", color="kind", title="Query volume over time"))

            top_terms = Counter(df["query"].str.lower())
            st.write("Most frequent queries")
            st.dataframe(pd.DataFrame(top_terms.most_common(10), columns=["query", "count"]))
    else:
        st.info("No queries logged yet — try Search or Chat first.")

    st.caption(
        "Document-cluster visualization (UMAP/PCA over chunk embeddings) can be added "
        "once you expose an /embeddings endpoint from the backend — flagging as a next step."
    )
