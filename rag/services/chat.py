from .retrieval import retrieve_relevant_chunks
from .generation import generate_answer
from django.core.cache import cache



def get_bot_response(bot, question, relevance_criteria=None):
    chunks = []
    if bot.uses_rag:
        chunks = retrieve_relevant_chunks(bot, question)

    answer, usage = generate_answer(bot, question, chunks, relevance_criteria=relevance_criteria)
    return answer, usage


def get_bot_cached(bot_id, ttl=300):
    key = f"bot:{bot_id}"
    bot = cache.get(key)
    if bot is None:
        from clients.models import Bot
        bot = Bot.objects.get(id=bot_id)
        cache.set(key, bot, ttl)
    return bot