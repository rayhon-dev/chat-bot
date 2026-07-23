from openai import OpenAI
import os


def build_context(chunks):
    if not chunks:
        return ""
    parts = []
    for chunk in chunks:
        source = chunk.document.original_filename
        parts.append(f"[Manba: {source}]\n{chunk.chunk_text}")
    return "\n\n---\n\n".join(parts)

PROVIDER_CONFIG = {
    "openai": {
        "base_url": None,  # standart OpenAI
        "env_key": "PLATFORM_OPENAI_API_KEY",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "env_key": "DEEPSEEK_API_KEY",
    },
}



def get_llm_api_key(bot):
    if bot.api_key_source == bot.ApiKeySource.CLIENT and bot.client_api_key:
        return bot.client_api_key
    config = PROVIDER_CONFIG.get(bot.llm_provider, PROVIDER_CONFIG["openai"])
    return os.getenv(config["env_key"])


def get_llm_client(bot):
    config = PROVIDER_CONFIG.get(bot.llm_provider, PROVIDER_CONFIG["openai"])
    api_key = get_llm_api_key(bot)
    return OpenAI(api_key=api_key, base_url=config["base_url"])

def generate_answer(bot, question, chunks, relevance_criteria=None):
    context = build_context(chunks)
    system_prompt = bot.system_prompt or "Siz yordamchi botsiz."

    relevance_instruction = ""
    if relevance_criteria:
        relevance_instruction = (
            f"\n\nMUHIM: Agar foydalanuvchi savoli quyidagi mavzuga aloqasi bo'lmasa: "
            f"\"{relevance_criteria}\", unda faqat 'SKIP' so'zini qaytaring, boshqa hech narsa yozmang."
        )

    if context:
        user_prompt = (
            f"Quyidagi ma'lumotlar asosida savolga javob bering.{relevance_instruction}\n\n"
            f"Ma'lumotlar:\n{context}\n\n"
            f"Savol: {question}"
        )
    else:
        if bot.uses_rag:
            return bot.fallback_message or "Kechirasiz, javob topa olmadim."
        user_prompt = question + relevance_instruction

    client = get_llm_client(bot)

    response = client.chat.completions.create(
        model=bot.llm_model or "gpt-4o-mini",
        temperature=bot.temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    answer = response.choices[0].message.content.strip()

    if answer == "SKIP":
        return None

    return answer