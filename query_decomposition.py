"""
Query Decomposition
====================
Detects multi-part questions and splits them into sub-queries,
runs separate retrievals for each, then merges contexts before
sending to the LLM. This fixes the cross-domain query failure
where mixing unrelated topics in one question caused retrieval bias.
"""

import re
from typing import List


# Signal phrases that indicate a multi-part question
SPLIT_PATTERNS = [
    r"\band\b",          # "what is X and how does Y work"
    r"\balso\b",         # "what is X, also explain Y"
    r"\badditionally\b", # "explain X, additionally what is Y"
    r"\bmoreover\b",
    r"\bfurthermore\b",
    r"\bas well as\b",
    r"\balong with\b",
]

# Minimum length for a sub-query to be worth retrieving separately
MIN_SUBQUERY_LENGTH = 15


def split_query(query: str) -> List[str]:
    """
    Split a multi-part question into individual sub-queries.
    Returns a list with one item if no split is needed.
    """
    query = query.strip()

    # Check if query contains question marks — multiple ?'s = definitely multi-part
    parts_by_question = [p.strip() for p in query.split("?") if len(p.strip()) > MIN_SUBQUERY_LENGTH]
    if len(parts_by_question) > 1:
        return [p + "?" for p in parts_by_question]

    # Check for comma + conjunction patterns like "explain X, and what is Y"
    comma_and = re.split(r",\s*(?:and|also|additionally)\s+", query, flags=re.IGNORECASE)
    if len(comma_and) > 1 and all(len(p) > MIN_SUBQUERY_LENGTH for p in comma_and):
        return [p.strip() for p in comma_and]

    # Check for sentence-level splits on conjunctions
    # Only split if both halves look like independent questions
    for pattern in SPLIT_PATTERNS:
        parts = re.split(pattern, query, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) == 2:
            part_a, part_b = parts[0].strip(), parts[1].strip()
            # Only split if both halves are substantial
            if len(part_a) > MIN_SUBQUERY_LENGTH and len(part_b) > MIN_SUBQUERY_LENGTH:
                # Check if they look like different topics (naive: different first nouns)
                words_a = set(part_a.lower().split()[:5])
                words_b = set(part_b.lower().split()[:5])
                overlap = words_a & words_b - {"what", "how", "is", "are", "the", "a", "an", "do", "does"}
                if len(overlap) == 0:
                    return [part_a, part_b]

    # No split needed — return as single query
    return [query]


def decompose_and_retrieve(query: str, vectorstore, k_per_subquery: int = 6):
    """
    Run query decomposition and retrieve contexts for each sub-query.
    Returns merged list of unique documents and the sub-queries used.
    """
    sub_queries = split_query(query)

    all_docs = []
    seen_ids = set()

    for sub_query in sub_queries:
        results = vectorstore.similarity_search(sub_query, k=k_per_subquery)
        for doc in results:
            # Deduplicate by content hash
            doc_id = hash(doc.page_content[:100])
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                all_docs.append(doc)

    return all_docs, sub_queries
