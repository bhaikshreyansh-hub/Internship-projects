"""
Dataset Builder: AI & Machine Learning Knowledge Base
======================================================
Downloads 40+ Wikipedia articles on AI/ML topics and saves them as
.txt files into raw_documents/, ready for ingestion + embedding.

Run from project root (venv activated):
    pip install wikipedia-api
    python build_dataset.py

After this finishes, run:
    python ingest_documents.py
    python chunk_and_embed.py
"""

import os
import time
import re
from pathlib import Path

try:
    import wikipediaapi
except ImportError:
    print("ERROR: Run 'pip install wikipedia-api' first.")
    exit(1)

OUTPUT_DIR = Path("./raw_documents/ai_ml_dataset")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 40+ AI/ML topics spanning core ML, deep learning, NLP, CV, RL, and AI ethics
TOPICS = [
    # Core Machine Learning
    "Machine learning",
    "Supervised learning",
    "Unsupervised learning",
    "Reinforcement learning",
    "Deep learning",
    "Neural network (machine learning)",
    "Overfitting",
    "Cross-validation (statistics)",
    "Feature engineering",
    "Dimensionality reduction",

    # Algorithms
    "Linear regression",
    "Logistic regression",
    "Decision tree",
    "Random forest",
    "Support vector machine",
    "K-nearest neighbors algorithm",
    "K-means clustering",
    "Principal component analysis",
    "Gradient descent",
    "Backpropagation",

    # Deep Learning Architectures
    "Convolutional neural network",
    "Recurrent neural network",
    "Long short-term memory",
    "Transformer (deep learning architecture)",
    "Generative adversarial network",
    "Autoencoder",
    "Attention (machine learning)",
    "BERT (language model)",

    # NLP
    "Natural language processing",
    "Word2vec",
    "Sentiment analysis",
    "Named-entity recognition",
    "Machine translation",
    "Text summarization",

    # Computer Vision
    "Computer vision",
    "Object detection",
    "Image segmentation",
    "Facial recognition system",

    # AI General
    "Artificial intelligence",
    "Expert system",
    "Knowledge representation and reasoning",
    "Artificial general intelligence",
    "AI safety",
    "Algorithmic bias",
    "Explainable artificial intelligence",

    # Applications
    "Recommender system",
    "Autonomous vehicle",
    "Speech recognition",
]

def sanitize_filename(title: str) -> str:
    return re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_').lower()[:80]

def download_articles():
    wiki = wikipediaapi.Wikipedia(
        language='en',
        user_agent='EKB-InternshipProject/1.0 (educational use)'
    )

    success, skipped, failed = 0, 0, 0

    print(f"Downloading {len(TOPICS)} Wikipedia articles on AI/ML...\n")

    for i, topic in enumerate(TOPICS, 1):
        fname = OUTPUT_DIR / f"{sanitize_filename(topic)}.txt"

        if fname.exists():
            print(f"[{i:02d}/{len(TOPICS)}] SKIP (already exists): {topic}")
            skipped += 1
            continue

        page = wiki.page(topic)

        if not page.exists():
            print(f"[{i:02d}/{len(TOPICS)}] NOT FOUND: {topic}")
            failed += 1
            continue

        # Write title + full text so the LLM has context on what it's reading
        content = f"# {page.title}\n\n{page.text}"

        if len(content) < 500:
            print(f"[{i:02d}/{len(TOPICS)}] TOO SHORT, skipping: {topic}")
            failed += 1
            continue

        fname.write_text(content, encoding="utf-8")
        word_count = len(content.split())
        print(f"[{i:02d}/{len(TOPICS)}] OK ({word_count:,} words): {topic}")
        success += 1
        time.sleep(0.5)   # be polite to Wikipedia's servers

    print(f"\n{'='*50}")
    print(f"Downloaded : {success}")
    print(f"Skipped    : {skipped} (already existed)")
    print(f"Failed     : {failed}")
    print(f"Total files: {len(list(OUTPUT_DIR.glob('*.txt')))}")
    print(f"\nAll articles saved to: {OUTPUT_DIR}")
    print("\nNext steps:")
    print("  python ingest_documents.py")
    print("  python chunk_and_embed.py")

if __name__ == "__main__":
    download_articles()
