import tempfile
import os

from ..models import Chunk
from .parser import extract_text_with_pages
from .chunker import chunk_pages
from .embedder import get_embeddings_batch, get_embedding_model, EMBEDDING_DIMENSIONS
from .dynamic_params import calculate_chunk_params
from rag.services.milvus_client import ensure_collection, insert_vectors


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

    total_length = sum(len(text) for text, _ in pages)
    params = calculate_chunk_params(total_length)

    chunks_with_pages = chunk_pages(
        pages,
        chunk_size=params["chunk_size"],
        overlap=params["overlap"],
    )

    if not chunks_with_pages:
        raise ValueError("Fayldan matn ajratib bo'lmadi (bo'sh natija)")

    return chunks_with_pages, params


def _get_or_create_collection_name(bot):
    if bot.milvus_collection_name:
        return bot.milvus_collection_name

    collection_name = f"bot_{bot.id}"
    bot.milvus_collection_name = collection_name
    bot.save(update_fields=["milvus_collection_name"])
    return collection_name


def _save_chunks_and_vectors(document, bot, chunks_with_pages, vectors, collection_name):
    starting_id = Chunk.objects.filter(document__bot=bot).count()

    milvus_entries = []
    for index, (chunk_text, page_number) in enumerate(chunks_with_pages):
        vector_id = starting_id + index

        Chunk.objects.create(
            document=document,
            chunk_text=chunk_text,
            chunk_index=index,
            page_number=page_number,
            milvus_vector_id=str(vector_id),
        )

        milvus_entries.append({"id": vector_id, "vector": vectors[index]})

    insert_vectors(collection_name, milvus_entries)


def _maybe_update_bot_top_k(bot, recommended_top_k):
    if recommended_top_k > bot.default_top_k:
        bot.default_top_k = recommended_top_k
        bot.save(update_fields=["default_top_k"])


def process_document(document):
    bot = document.bot

    document.status = "processing"
    document.save(update_fields=["status"])

    try:
        tmp_path = _save_temp_file(document)
        chunks_with_pages, params = _extract_and_chunk(tmp_path, document)

        chunk_texts = [text for text, _ in chunks_with_pages]

        model = get_embedding_model(bot)
        dimension = EMBEDDING_DIMENSIONS.get(model, 1536)
        collection_name = _get_or_create_collection_name(bot)

        ensure_collection(collection_name, dimension)

        vectors = get_embeddings_batch(bot, chunk_texts, batch_size=100)

        _save_chunks_and_vectors(document, bot, chunks_with_pages, vectors, collection_name)

        document.status = "ready"
        document.chunk_count = len(chunks_with_pages)
        document.save(update_fields=["status", "chunk_count"])

        _maybe_update_bot_top_k(bot, params["top_k"])

    except Exception as e:
        document.status = "failed"
        document.save(update_fields=["status"])
        raise e