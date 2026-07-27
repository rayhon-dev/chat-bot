import os
from openai import OpenAI
from sentence_transformers import SentenceTransformer

_local_model = None
LOCAL_MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"
LOCAL_DIMENSION = 768

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "local": LOCAL_DIMENSION,
}


def get_local_model():
    global _local_model
    if _local_model is None:
        _local_model = SentenceTransformer(LOCAL_MODEL_NAME)
    return _local_model


def get_embeddings_batch_local(texts, batch_size=64):
    model = get_local_model()
    all_vectors = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        vectors = model.encode(batch, convert_to_numpy=True, show_progress_bar=False)
        all_vectors.extend([v.tolist() for v in vectors])
    return all_vectors


def get_api_key(bot):
    if bot.embedding_model == "local":
        return None
    if bot.api_key_source == "client":
        if not bot.client_api_key:
            raise ValueError(f"Bot '{bot.name}' uchun client_api_key kiritilmagan")
        return bot.client_api_key
    return os.getenv("PLATFORM_OPENAI_API_KEY")


def get_embedding_model(bot):
    return bot.embedding_model or DEFAULT_EMBEDDING_MODEL


def get_embeddings_batch(bot, texts, batch_size=100):
    if bot.embedding_model == "local":
        return get_embeddings_batch_local(texts, batch_size=batch_size)

    api_key = get_api_key(bot)
    model = get_embedding_model(bot)
    client = OpenAI(api_key=api_key)

    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = client.embeddings.create(input=batch, model=model)
        all_embeddings.extend([item.embedding for item in response.data])
    return all_embeddings