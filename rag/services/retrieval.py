import re
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F
from ingestion.models import Chunk
from ingestion.services.embedder import get_embeddings_batch
from .milvus_client import search_vectors

CANDIDATE_K = 30
FINAL_K = 6
RRF_K = 60
MIN_DENSE_SCORE = 0.42


def _keyword_search(bot, query_text, limit=CANDIDATE_K):
    words = [t for t in re.findall(r"\w+", query_text.lower()) if len(t) > 3]
    if not words:
        return []

    words_sorted = sorted(set(words), key=len, reverse=True)
    top_words = words_sorted[:4]

    qs = Chunk.objects.filter(document__bot=bot)
    combined_score = None

    for i, word in enumerate(top_words):
        field_name = f"rank_{i}"
        q = SearchQuery(word, config="simple")
        qs = qs.annotate(**{field_name: SearchRank(F("search_vector"), q)})
        weighted_term = F(field_name) * (len(word) ** 2)
        combined_score = weighted_term if combined_score is None else combined_score + weighted_term

    qs = (
        qs.annotate(combined_score=combined_score)
        .filter(combined_score__gt=0)
        .order_by("-combined_score")[:limit]
    )
    return list(qs)


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

    # Keyword natijalaridan allaqachon bor obyektlarni qayta ishlatamiz
    by_id = {c.milvus_vector_id: c for c in keyword_chunks}

    # Faqat KEYWORD'da bo'lmagan (ya'ni faqat dense'dan kelgan) ID'lar uchun
    # qo'shimcha so'rov qilamiz
    missing_ids = [cid for cid in merged_ids if cid not in by_id]
    if missing_ids:
        extra_chunks = Chunk.objects.filter(
            document__bot=bot, milvus_vector_id__in=missing_ids
        ).select_related("document")
        for c in extra_chunks:
            by_id[c.milvus_vector_id] = c

    ordered = [by_id[cid] for cid in merged_ids if cid in by_id]

    print(f"\n--- SAVOL: {query_text} ---")
    print(f"--- dense: {len(dense_ids)}, keyword: {len(keyword_ids)}, yakuniy: {len(ordered)} ---")
    for i, c in enumerate(ordered):
        print(f"{i+1}: {c.chunk_text[:100]}...")
    print("---------------------------\n")

    return ordered