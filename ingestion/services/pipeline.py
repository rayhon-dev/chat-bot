import tempfile
import os
from ..models import Chunk
from .parser import extract_text_with_pages
from .embedder import get_embeddings_batch, get_embedding_model, EMBEDDING_DIMENSIONS, get_api_key
from rag.services.milvus_client import ensure_collection, insert_vectors
from ingestion.services.chunker import chunk_pages
from rag.constants import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE
from django.contrib.postgres.search import SearchVector


def _save_temp_file(document):
    file_extension = os.path.splitext(document.original_filename)[1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp:
        with document.file.open('rb') as source_file:
            tmp.write(source_file.read())
        return tmp.name


def _extract_and_chunk(tmp_path, document):
    try:
        pages = extract_text_with_pages(tmp_path, document.original_filename)
    finally:
        os.unlink(tmp_path)

    bot = document.bot

    chunks_with_pages = chunk_pages(
        pages,
        chunk_size=DEFAULT_CHUNK_SIZE,
        overlap=DEFAULT_CHUNK_OVERLAP,
        embedding_api_key=get_api_key(bot),
    )

    if not chunks_with_pages:
        raise ValueError("Fayldan matn ajratib bo'lmadi (bo'sh natija)")

    return chunks_with_pages

def _get_or_create_collection_name(bot):
    if bot.milvus_collection_name:
        return bot.milvus_collection_name

    collection_name = f"bot_{bot.id}"
    bot.milvus_collection_name = collection_name
    bot.save(update_fields=["milvus_collection_name"])
    return collection_name


def _save_chunks_and_vectors(document, chunks_with_pages, vectors, collection_name):
    # 1-QADAM: barcha Chunk obyektlarini BITTA so'rovda yaratamiz
    chunk_objects = [
        Chunk(
            document=document,
            chunk_text=chunk_text,
            chunk_index=index,
            page_number=page_number,
            milvus_vector_id="",
        )
        for index, (chunk_text, page_number) in enumerate(chunks_with_pages)
    ]
    created_chunks = Chunk.objects.bulk_create(chunk_objects)

    # 2-QADAM: endi har birining haqiqiy ID'si bor (PostgreSQL bulk_create
    # bilan ID qaytaradi), milvus_vector_id'ni xotirada belgilaymiz
    milvus_entries = []
    for chunk, vector in zip(created_chunks, vectors):
        chunk.milvus_vector_id = str(chunk.id)
        milvus_entries.append({"id": chunk.id, "vector": vector})

    # 3-QADAM: barcha milvus_vector_id'larni BITTA so'rovda yangilaymiz
    Chunk.objects.bulk_update(created_chunks, ["milvus_vector_id"])

    # Milvus'ga yozish (bu DB so'rovi emas, Milvus so'rovi)
    insert_vectors(collection_name, milvus_entries)

    # search_vector'ni to'ldirish (bitta so'rov, o'zgarishsiz qoladi)
    Chunk.objects.filter(document=document).update(
        search_vector=SearchVector("chunk_text", config="simple")
    )



def process_document(document):
    bot = document.bot

    old_vector_ids = list(
        Chunk.objects.filter(document=document).values_list('milvus_vector_id', flat=True)
    )

    document.status = "processing"
    document.save(update_fields=["status"])

    try:
        tmp_path = _save_temp_file(document)
        chunks_with_pages = _extract_and_chunk(tmp_path, document)

        chunk_texts = [text for text, _ in chunks_with_pages]

        model = get_embedding_model(bot)
        dimension = EMBEDDING_DIMENSIONS.get(model, 1536)
        collection_name = _get_or_create_collection_name(bot)

        if old_vector_ids:
            from rag.services.milvus_client import get_client
            client = get_client()
            if client.has_collection(collection_name=collection_name):
                valid_ids = [int(vid) for vid in old_vector_ids if vid]
                if valid_ids:
                    client.delete(collection_name=collection_name, ids=valid_ids)
            Chunk.objects.filter(document=document).delete()

        ensure_collection(collection_name, dimension)

        vectors = get_embeddings_batch(bot, chunk_texts, batch_size=100)

        _save_chunks_and_vectors(document, chunks_with_pages, vectors, collection_name)

        document.status = "ready"
        document.chunk_count = len(chunks_with_pages)
        document.save(update_fields=["status", "chunk_count"])

    except Exception as e:
        document.status = "failed"
        document.save(update_fields=["status"])
        raise e