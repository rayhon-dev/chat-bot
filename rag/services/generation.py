from openai import OpenAI
import requests
import os
from .pricing import calculate_cost


def build_context(chunks):
    if not chunks:
        return ""
    parts = []
    for chunk in chunks:
        source = chunk.document.original_filename
        parts.append(f"[Manba: {source}]\n{chunk.chunk_text}")
    return "\n\n---\n\n".join(parts)


PROVIDER_CONFIG = {
    "openai":   {"base_url": None, "env_key": "PLATFORM_OPENAI_API_KEY"},
    "deepseek": {"base_url": "https://api.deepseek.com", "env_key": "DEEPSEEK_API_KEY"},
    "cloudapi": {"base_url": "https://cloudapi.uz/api/v1", "env_key": "CLOUDAPI_API_KEY"},
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


def _call_cloudapi_direct(bot, model_name, system_prompt, user_prompt):

    api_key = get_llm_api_key(bot)
    resp = requests.post(
        "https://cloudapi.uz/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model_name,
            "temperature": bot.temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    answer = data["choices"][0]["message"]["content"].strip()
    prompt_tokens = data["usage"]["prompt_tokens"]
    completion_tokens = data["usage"]["completion_tokens"]
    usage = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": data["usage"]["total_tokens"],
        "model": model_name,
        "cost_usd": calculate_cost(model_name, prompt_tokens, completion_tokens),
    }
    return answer, usage


def generate_answer(bot, question, chunks, relevance_criteria=None):
    FORMATTING_RULES = """
    
    FORMATLASH QOIDALARI (har doim rioya qiling):
    - Formulalarni LaTeX belgilarisiz (\\[ \\], $$, \\( \\) ishlatmasdan), oddiy matn ko'rinishida yoz. Masalan: "GDP = C + I + G + (X - M)" deb yoz.
    - Markdown belgilarini (**, ###, ---) ishlatma — oddiy, sodda matn yoz.
    - Har bir yangi fikr yoki ro'yxat elementini yangi qatordan boshla.
    - Ro'yxatlarda har bir band uchun raqam yoki chiziqcha qo'yib, alohida qatorga yoz.
    """

    context = build_context(chunks)
    system_prompt = (bot.system_prompt or "Siz yordamchi botsiz.") + FORMATTING_RULES

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
            if relevance_criteria:
                return None, None
            return (bot.fallback_message or "Kechirasiz, javob topa olmadim."), None
        user_prompt = question + relevance_instruction

    model_name = bot.llm_model or "gpt-4o-mini"

    if bot.llm_provider == "cloudapi":
        answer, usage = _call_cloudapi_direct(bot, model_name, system_prompt, user_prompt)
    else:
        client = get_llm_client(bot)
        response = client.chat.completions.create(
            model=model_name,
            temperature=bot.temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        answer = response.choices[0].message.content.strip()
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
            "model": model_name,
            "cost_usd": calculate_cost(model_name, response.usage.prompt_tokens, response.usage.completion_tokens),
        }

    if answer == "SKIP":
        return None, usage

    return answer, usage