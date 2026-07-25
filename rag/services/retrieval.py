import re
from django.contrib.postgres.search import SearchQuery, SearchRank

from ingestion.models import Chunk
from ingestion.services.embedder import get_embeddings_batch
from .milvus_client import search_vectors

CANDIDATE_K = 30
FINAL_K = 6
RRF_K = 60
MIN_DENSE_SCORE = 0.42
STOPWORDS = {"uchun", "bilan", "boʻyicha", "boyicha", "qanday", "necha", "kerak", "mumkin", "hisoblanadi"}


def _build_keyword_query(query_text):
    terms = [t for t in re.findall(r"\w+", query_text.lower()) if len(t) > 3 and t not in STOPWORDS]
    if not terms:
        return None
    q = SearchQuery(terms[0], config="simple")
    for t in terms[1:]:
        q = q | SearchQuery(t, config="simple")
    return q


def _keyword_search(bot, query_text, limit=CANDIDATE_K):
    q = _build_keyword_query(query_text)
    if q is None:
        return []
    return list(
        Chunk.objects
        .filter(document__bot=bot, search_vector=q)
        .annotate(rank=SearchRank("search_vector", q))
        .order_by("-rank")[:limit]
    )


def _dense_search(bot, query_text, limit=CANDIDATE_K):
    query_vector = get_embeddings_batch(bot, [query_text], batch_size=1)[0]
    results = search_vectors(bot.milvus_collection_name, query_vector, top_k=limit)
    if not results or not results[0]:
        return [], 0.0
    hits = results[0]
    return [str(h["id"]) for h in hits], hits[0]["distance"]


def _rrf_merge(dense_ids, keyword_ids, final_k):
    scores = {}
    for rank, cid in enumerate(dense_ids):
        scores[cid] = scores.get(cid, 0) + 1 / (RRF_K + rank + 1)
    for rank, cid in enumerate(keyword_ids):
        scores[cid] = scores.get(cid, 0) + 1 / (RRF_K + rank + 1)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [cid for cid, _ in ranked[:final_k]]


def retrieve_relevant_chunks(bot, query_text, top_k=None):
    if not bot.milvus_collection_name:
        return []

    final_k = top_k or FINAL_K

    dense_ids, best_dense_score = _dense_search(bot, query_text)
    keyword_chunks = _keyword_search(bot, query_text)
    keyword_ids = [c.milvus_vector_id for c in keyword_chunks]

    if best_dense_score < MIN_DENSE_SCORE and not keyword_ids:
        return []

    merged_ids = _rrf_merge(dense_ids, keyword_ids, final_k)
    if not merged_ids:
        return []

    chunks = Chunk.objects.filter(
        document__bot=bot, milvus_vector_id__in=merged_ids
    ).select_related("document")
    by_id = {c.milvus_vector_id: c for c in chunks}
    ordered = [by_id[cid] for cid in merged_ids if cid in by_id]

    print(f"\n--- SAVOL: {query_text} ---")
    print(f"--- dense: {len(dense_ids)}, keyword: {len(keyword_ids)}, yakuniy: {len(ordered)} ---")
    for i, c in enumerate(ordered):
        print(f"{i+1}: {c.chunk_text[:100]}...")
    print("---------------------------\n")

    return ordered