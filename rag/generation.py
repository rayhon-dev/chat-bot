import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_answer(question, context_chunks):
    """
    Topilgan chunklar asosida savolga javob generatsiya qiladi.
    """
    context_text = "\n\n".join(context_chunks)

    system_prompt = """Sen faqat berilgan kontekst asosida javob beruvchi yordamchisan.

QOIDALAR:
1. Faqat pastda berilgan kontekstdagi ma'lumotdan foydalan
2. Agar javob kontekstda bo'lmasa, aniq shunday de: "Bu ma'lumot yuklangan hujjatlarda topilmadi"
3. O'zingning umumiy bilimingdan hech narsa qo'shma
4. Javobni o'zbek tilida, aniq va qisqa yoz
"""

    user_prompt = f"""Kontekst:
{context_text}

Savol: {question}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    return response.choices[0].message.content
