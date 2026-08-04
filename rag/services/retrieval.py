import logging
import re
from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException
from django.contrib.postgres.search import SearchQuery, SearchRank
from ingestion.models import Chunk, Document
from ingestion.services.embedder import get_embeddings_batch
from .milvus_client import search_vectors
from chatbot_project.settings import CANDIDATE_K, FINAL_K, RRF_K
from langfuse import observe, get_client
logger = logging.getLogger(__name__)

MIN_DENSE_SCORE = 0.42


@observe(name="Smart_Translate")
def smart_translate(text: str, target_lang: str = "en") -> str:

    if not target_lang:
        target_lang = "en"

    target_lang = target_lang.lower()

    try:
        detected_lang = detect(text)
        logger.info(f"Detected language: '{detected_lang}', Target language: '{target_lang}'")

        # Savol va fayl tili bir xil bo'lsa tarjima qilmaymiz
        if detected_lang == target_lang:
            logger.info(f"Savol va fayl tili bir xil ({detected_lang}). Tarjima qilinmadi.")
            return text

        # Tillar har xil bo'lsa tarjima qilamiz
        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
        logger.info(f"Savol ({detected_lang}) -> Fayl tiliga ({target_lang}) tarjima qilindi: '{translated}'")
        return translated

    except LangDetectException:
        logger.warning("Language detection failed. Returning raw text.")
        return text
    except Exception as e:
        logger.warning(f"Translation failed: {e}. Returning raw text.")
        return text

@observe(name="Keyword_Search")
def _keyword_search(bot, query_text, limit=CANDIDATE_K):
    words = [t for t in re.findall(r"[\w'ʻʼ‘’]+", query_text.lower()) if len(t) > 2]
    if not words:
        return []

    term_freq = bot.term_frequencies or {}

    def rarity_score(word):
        freq = term_freq.get(word, 1.0)
        return 1.0 / (freq + 0.01)

    unique_words = list(set(words))
    words_sorted = sorted(unique_words, key=rarity_score, reverse=True)
    top_words = words_sorted[:5]
    if not top_words:
        return []

    query_expression = SearchQuery(top_words[0], config="simple")
    for word in top_words[1:]:
        query_expression |= SearchQuery(word, config="simple")

    # 1-bosqich: Postgres orqali kengroq kandidatlar to'plamini olamiz (masalan 2x limit)
    candidates = list(
        Chunk.objects.filter(document__bot=bot, search_vector=query_expression)
        .annotate(rank=SearchRank("search_vector", query_expression))
        .only("id", "chunk_text", "milvus_vector_id")
        .order_by("-rank")[: limit * 2]
    )

    # 2-bosqich: sizning IDF (rarity_score) asosida qayta ballaymiz — DB'ga qo'shimcha so'rovsiz,
    # chunki candidates allaqachon xotirada
    def idf_boost(chunk):
        text_lower = chunk.chunk_text.lower()
        return sum(rarity_score(w) for w in top_words if w in text_lower)

    candidates.sort(key=idf_boost, reverse=True)
    return candidates[:limit]


@observe(name="Dense_Search")
def _dense_search(bot, query_text, limit=CANDIDATE_K):
    query_vector = get_embeddings_batch(bot, [query_text], batch_size=1)[0]
    results = search_vectors(bot.milvus_collection_name, query_vector, top_k=limit)
    if not results or not results[0]:
        return [], 0.0
    hits = results[0]
    best_score = hits[0]["distance"] if hits else 0.0

    valid_hits = [h for h in hits if h.get("distance", 0.0) >= MIN_DENSE_SCORE]

    return [str(h["id"]) for h in valid_hits], best_score


def _rrf_merge(dense_ids, keyword_ids, final_k):
    scores = {}
    for rank, cid in enumerate(dense_ids):
        scores[cid] = scores.get(cid, 0) + 1 / (RRF_K + rank + 1)
    for rank, cid in enumerate(keyword_ids):
        scores[cid] = scores.get(cid, 0) + 1 / (RRF_K + rank + 1)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [cid for cid, _ in ranked[:final_k]]


@observe(name="RAG_Retrieve_Chunks")
def retrieve_relevant_chunks(bot, query_text, top_k=None):
    if not bot.milvus_collection_name:
        return []

    final_k = top_k or FINAL_K

    document_language = (
        Document.objects.filter(bot=bot)
        .values_list("language", flat=True)
        .first()
    )
    target_language = document_language or "en"
    translated_query = smart_translate(query_text, target_lang=target_language)

    dense_ids, best_dense_score = _dense_search(bot, translated_query)
    keyword_chunks = _keyword_search(bot, translated_query)
    keyword_ids = [c.milvus_vector_id for c in keyword_chunks]

    get_client().update_current_span(
        input={
            "query_text": query_text,
            "translated_query": translated_query,
            "target_language": target_language
        },
        metadata={
            "bot_id": bot.id,
            "dense_count": len(dense_ids),
            "keyword_count": len(keyword_ids),
            "best_dense_score": float(best_dense_score),
            "min_dense_score_threshold": MIN_DENSE_SCORE,
        }
    )

    if not dense_ids and not keyword_ids:
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