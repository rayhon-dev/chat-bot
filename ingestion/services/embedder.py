import os
from openai import OpenAI

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
}


def get_api_key(bot):
    if bot.api_key_source == "client":
        if not bot.client_api_key:
            raise ValueError(f"Bot '{bot.name}' uchun client_api_key kiritilmagan")
        return bot.client_api_key
    return os.getenv("PLATFORM_OPENAI_API_KEY")


def get_embedding_model(bot):
    return bot.embedding_model or DEFAULT_EMBEDDING_MODEL


def get_embeddings_batch(bot, texts, batch_size=100):
    api_key = get_api_key(bot)
    model = get_embedding_model(bot)
    client = OpenAI(api_key=api_key)

    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = client.embeddings.create(input=batch, model=model)
        all_embeddings.extend([item.embedding for item in response.data])
    return all_embeddings