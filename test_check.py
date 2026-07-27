# test_real_context.py
import requests

resp = requests.post(
    "https://cloudapi.uz/api/v1/chat/completions",
    headers={
        "Authorization": "Bearer cap-35e50f5f20a0e3f997cdb127ee3f87f0",
        "Content-Type": "application/json",
    },
    json={
        "model": "openai/gpt-4o-mini-2024-07-18",
        "messages": [
            {"role": "system", "content": "Sen O'zbekiston Respublikasi Mehnat kodeksi bo'yicha maslahat beruvchi yordamchisan."},
            {"role": "user", "content": "Xodimga foydalanilmagan barcha har yilgi asosiy va qoʻshimcha taʼtillar uchun pul kompensatsiyasi qachon toʻliq toʻlab beriladi?"}
        ],
    },
)
print("STATUS:", resp.status_code)
print("BODY:", resp.text[:500])