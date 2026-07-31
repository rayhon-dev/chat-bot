import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from collections import Counter
import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"


GENERIC_NUMBERED_UNIT_PATTERN = re.compile(
    r'\n\s*(\d{1,4})\s*[-.]?\s*([A-Za-zА-Яа-яЎўҚқҒғҲҳʻʼ]{3,20})\.',
    re.IGNORECASE
)

def detect_dynamic_structure_word(text, sample_size=15000):
    sample = text[:sample_size]
    matches = GENERIC_NUMBERED_UNIT_PATTERN.findall(sample)
    if len(matches) < 3:
        return None
    word_counts = Counter(word.lower() for _, word in matches)
    most_common_word, count = word_counts.most_common(1)[0]
    if count < 3:
        return None
    return most_common_word


def build_dynamic_pattern(structure_word):
    escaped_word = re.escape(structure_word)
    return re.compile(rf'\n(?=\s*\d{{1,4}}\s*[-.]?\s*{escaped_word}\.)', re.IGNORECASE)


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
    detected = detect_dynamic_structure_word(text)

    if detected:
        pattern = build_dynamic_pattern(detected)
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