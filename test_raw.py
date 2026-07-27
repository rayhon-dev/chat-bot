# test_models.py
import requests

API_KEY = "cap-44e965dc4cfa1265abb42295815caff4"

models = [
    "openai/gpt-oss-20b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
]

for m in models:
    resp = requests.post(
        "https://cloudapi.uz/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": m, "messages": [{"role": "user", "content": "Salom! O'zbekcha javob ber: 2+2 nechchi?"}]},
    )
    if resp.status_code == 200:
        data = resp.json()
        answer = data["choices"][0]["message"]["content"][:120]
        print(f"✅ {m}\n   → {answer}\n")
    else:
        print(f"❌ {m}  ({resp.status_code})\n   → {resp.text[:150]}\n")