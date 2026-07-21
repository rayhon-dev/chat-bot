from .retrieval import retrieve_relevant_chunks
from .generation import generate_answer


def get_bot_response(bot, question):
    chunks = []
    if bot.uses_rag:
        chunks = retrieve_relevant_chunks(bot, question)

    answer = generate_answer(bot, question, chunks)
    return answer