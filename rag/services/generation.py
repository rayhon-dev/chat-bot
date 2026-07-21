from openai import OpenAI


def build_context(chunks):
    if not chunks:
        return ""
    parts = []
    for chunk in chunks:
        source = chunk.document.original_filename
        parts.append(f"[Manba: {source}]\n{chunk.chunk_text}")
    return "\n\n---\n\n".join(parts)


def get_llm_api_key(bot):
    if bot.api_key_source == bot.ApiKeySource.CLIENT and bot.client_api_key:
        return bot.client_api_key
    import os
    return os.getenv("PLATFORM_OPENAI_API_KEY")


def generate_answer(bot, question, chunks):
    context = build_context(chunks)

    system_prompt = bot.system_prompt or "Siz yordamchi botsiz."

    if context:
        user_prompt = (
            f"Quyidagi ma'lumotlar asosida savolga javob bering.\n\n"
            f"Ma'lumotlar:\n{context}\n\n"
            f"Savol: {question}"
        )
    else:
        if bot.uses_rag:
            return bot.fallback_message or "Kechirasiz, javob topa olmadim."
        user_prompt = question

    client = OpenAI(api_key=get_llm_api_key(bot))

    response = client.chat.completions.create(
        model=bot.llm_model or "gpt-4o-mini",
        temperature=bot.temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content