from openai import OpenAI
import os


def is_message_relevant(bot, text):
    if not bot.relevance_criteria:
        return True

    api_key = os.getenv("PLATFORM_OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    prompt = (
        f"Quyidagi xabar quyidagi mavzuga tegishli savolmi: \"{bot.relevance_criteria}\"?\n"
        f"Faqat 'ha' yoki 'yoq' deb javob ber, boshqa hech narsa yozma.\n\n"
        f"Xabar: \"{text}\""
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=5,
        messages=[{"role": "user", "content": prompt}],
    )

    answer = response.choices[0].message.content.strip().lower()
    return answer.startswith("ha")