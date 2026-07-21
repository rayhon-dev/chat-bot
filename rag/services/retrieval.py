from ingestion.models import Chunk
from ingestion.services.embedder import get_embeddings_batch
from .milvus_client import search_vectors


def retrieve_relevant_chunks(bot, query_text, top_k=None):
    if top_k is None:
        top_k = bot.default_top_k

    if not bot.milvus_collection_name:
        return []

    query_vector = get_embeddings_batch(bot, [query_text], batch_size=1)[0]

    results = search_vectors(bot.milvus_collection_name, query_vector, top_k=top_k)

    if not results or not results[0]:
        return []

    vector_ids = [str(hit["id"]) for hit in results[0]]

    chunks = Chunk.objects.filter(
        document__bot=bot,
        milvus_vector_id__in=vector_ids,
    ).select_related("document")

    chunks_by_id = {c.milvus_vector_id: c for c in chunks}
    ordered_chunks = [chunks_by_id[vid] for vid in vector_ids if vid in chunks_by_id]

    return ordered_chunks