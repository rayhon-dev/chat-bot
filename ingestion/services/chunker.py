import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings


STRICT_STRUCTURE_PATTERNS = {
    "legal_article_uz": re.compile(r'\n(?=\s*\d{1,4}\s*-\s*modda\.)', re.IGNORECASE),
    "legal_article_ru": re.compile(r'\n(?=\s*[Сс]татья\s+\d{1,4}\.)', re.IGNORECASE),
    "legal_paragraph_uz": re.compile(r'\n(?=\s*\d{1,4}\s*-\s*band\.)', re.IGNORECASE),
    "chapter_uz_ru": re.compile(r'\n(?=\s*(?:[Bb]ob|[Гг]лава)\s+\d+)'),
    "chapter_en": re.compile(r'\n(?=\s*Chapter\s+\d+)', re.IGNORECASE),
    "contract_clause": re.compile(r'\n(?=\s*\d{1,2}\.\d{1,2}\.\s)'),
}


def detect_strict_pattern(text, sample_size=5000):
    sample = text[:sample_size]
    best_pattern_name = None
    best_count = 0

    for name, pattern in STRICT_STRUCTURE_PATTERNS.items():
        count = len(pattern.findall(sample))
        if count > best_count:
            best_count = count
            best_pattern_name = name

    if best_count < 2:
        return None
    return best_pattern_name


def split_by_structure(text, pattern):
    parts = pattern.split(text)
    return [p.strip() for p in parts if p.strip()]


def _fallback_split(text, chunk_size, overlap):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    return splitter.split_text(text)



_local_embeddings = None


def _get_local_embeddings():
    global _local_embeddings
    if _local_embeddings is None:
        _local_embeddings = HuggingFaceEmbeddings(model_name="paraphrase-multilingual-mpnet-base-v2")
    return _local_embeddings


def _semantic_split(text, api_key=None):
    if api_key:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=api_key)
    else:
        embeddings = _get_local_embeddings()
    splitter = SemanticChunker(embeddings, breakpoint_threshold_type="percentile")
    return splitter.split_text(text)


def chunk_text_smart(text, chunk_size=1000, overlap=150, embedding_api_key=None):
    detected = detect_strict_pattern(text)

    if detected:
        pattern = STRICT_STRUCTURE_PATTERNS[detected]
        sections = split_by_structure(text, pattern)
        if len(sections) > 1:
            result = []
            for section in sections:
                if len(section) <= chunk_size:
                    result.append(section)
                else:
                    result.extend(_fallback_split(section, chunk_size, overlap))
            return result

    try:
        return _semantic_split(text, embedding_api_key)
    except Exception:
        return _fallback_split(text, chunk_size, overlap)


def chunk_pages(pages, chunk_size=1000, overlap=150, embedding_api_key=None):
    full_text = "\n".join(text for text, _ in pages)
    chunks = chunk_text_smart(
        full_text, chunk_size=chunk_size, overlap=overlap,
        embedding_api_key=embedding_api_key
    )
    return [(c, None) for c in chunks]