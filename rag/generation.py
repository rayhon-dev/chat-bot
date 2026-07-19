import os
from dotenv import load_dotenv
from openai import OpenAI
from langdetect import detect

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



def generate_answer(question, context_chunks):
    """
    Topilgan chunklar asosida savolga javob generatsiya qiladi.
    """
    context_text = "\n\n".join(context_chunks)

    try:
        lang_code = detect(question)
    except Exception:
        lang_code = "uz"

    lang_map = {
        "en": "ingliz (English)",
        "uz": "o'zbek",
        "ru": "rus (Russian)",
    }
    target_language = lang_map.get(lang_code, "o'zbek")

    system_prompt = f"""Sen faqat berilgan kontekst asosida javob beruvchi yordamchisan.

TIL BO'YICHA QAT'IY BUYRUQ:
Javobni FAQAT {target_language} tilida yoz. Boshqa tilda bironta ham so'z yozma.

QOLGAN QOIDALAR:
1. Faqat pastda berilgan kontekstdagi ma'lumotdan foydalan
2. Agar kontekstda savolga to'g'ridan-to'g'ri yoki bilvosita tegishli ma'lumot bo'lsa, shu asosida javob ber
3. Faqat kontekst savolga umuman aloqasi bo'lmasa, mos tilda "bu ma'lumot topilmadi" turidagi javob ber
4. O'zingning umumiy bilimingdan hech narsa qo'shma, faqat berilgan kontekstni talqin qil
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
