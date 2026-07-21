import tempfile
import os
from ..models import Chunk
from .parser import extract_text_with_pages
from .chunker import chunk_pages
from .embedder import get_embeddings_batch, get_embedding_model, EMBEDDING_DIMENSIONS
from .dynamic_params import calculate_chunk_params
from rag.services.milvus_client import ensure_collection, insert_vectors


def process_document(document):
    bot = document.bot
    document.status = "processing"
    document.save(update_fields=["status"])

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(document.original_filename)[1]) as tmp:
            with document.file.open('rb') as f:
                tmp.write(f.read())
            tmp_path = tmp.name

        try:
            pages = extract_text_with_pages(tmp_path, document.original_filename)
        finally:
            os.unlink(tmp_path)

        full_text_length = sum(len(p[0]) for p in pages)
        params = calculate_chunk_params(full_text_length)

        chunks_with_pages = chunk_pages(pages, chunk_size=params["chunk_size"], overlap=params["overlap"])
        chunk_texts = [c[0] for c in chunks_with_pages]

        if not chunk_texts:
            raise ValueError("Fayldan matn ajratib bo'lmadi (bo'sh natija)")

        model = get_embedding_model(bot)
        dimension = EMBEDDING_DIMENSIONS.get(model, 1536)

        collection_name = bot.milvus_collection_name or f"bot_{bot.id}"
        if not bot.milvus_collection_name:
            bot.milvus_collection_name = collection_name
            bot.save(update_fields=["milvus_collection_name"])

        ensure_collection(collection_name, dimension)

        vectors = get_embeddings_batch(bot, chunk_texts, batch_size=100)

        last_id = Chunk.objects.filter(document__bot=bot).count()

        milvus_entries = []
        for i, (chunk_text_value, page_number) in enumerate(chunks_with_pages):
            vector_id = last_id + i
            Chunk.objects.create(
                document=document,
                chunk_text=chunk_text_value,
                chunk_index=i,
                page_number=page_number,
                milvus_vector_id=str(vector_id),
            )
            milvus_entries.append({"id": vector_id, "vector": vectors[i]})

        insert_vectors(collection_name, milvus_entries)

        document.chunk_count = len(chunks_with_pages)
        document.status = "ready"
        document.save(update_fields=["status", "chunk_count"] if hasattr(document, "chunk_count") else ["status"])

    except Exception as e:
        document.status = "failed"
        document.save(update_fields=["status"])
        raise e

    if params["top_k"] > bot.default_top_k:
        bot.default_top_k = params["top_k"]
        bot.save(update_fields=["default_top_k"])