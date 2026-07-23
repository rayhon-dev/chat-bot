from ingestion.models import Chunk
from ingestion.services.embedder import get_embeddings_batch
from .milvus_client import search_vectors
from rag.constants import DEFAULT_TOP_K, MIN_ABSOLUTE_SCORE, RELATIVE_RATIO



def _filter_relevant_hits(hits):
    if not hits:
        return []

    best_score = hits[0]["distance"]

    if best_score < MIN_ABSOLUTE_SCORE:
        return []

    relative_threshold = best_score * RELATIVE_RATIO
    return [h for h in hits if h["distance"] >= relative_threshold]


def retrieve_relevant_chunks(bot, query_text, top_k=None):
    if top_k is None:
        top_k = DEFAULT_TOP_K

    if not bot.milvus_collection_name:
        return []

    query_vector = get_embeddings_batch(bot, [query_text], batch_size=1)[0]

    results = search_vectors(bot.milvus_collection_name, query_vector, top_k=top_k)

    if not results or not results[0]:
        return []

    filtered_hits = _filter_relevant_hits(results[0])

    if not filtered_hits:
        return []

    vector_ids = [str(hit["id"]) for hit in filtered_hits]

    chunks = Chunk.objects.filter(
        document__bot=bot,
        milvus_vector_id__in=vector_ids,
    ).select_related("document")

    chunks_by_id = {c.milvus_vector_id: c for c in chunks}
    ordered_chunks = [chunks_by_id[vid] for vid in vector_ids if vid in chunks_by_id]

    print(f"\n--- SAVOL: {query_text} ---")
    print(f"--- Milvus'dan {len(results[0])} ta nomzod, filtrdan keyin {len(ordered_chunks)} ta qoldi ---")
    for i, c in enumerate(ordered_chunks):
        print(f"{i + 1}: {c.chunk_text[:100]}...")
    print("---------------------------\n")

    return ordered_chunks