from .retrieval import retrieve_relevant_chunks
from .generation import generate_answer


def get_bot_response(bot, question, relevance_criteria=None):
    chunks = []
    if bot.uses_rag:
        chunks = retrieve_relevant_chunks(bot, question)

    answer, usage = generate_answer(bot, question, chunks, relevance_criteria=relevance_criteria)
    return answer, usage