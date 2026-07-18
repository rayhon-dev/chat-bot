import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_embedding(text):
    """
    Matnni vektorga aylantiradi (OpenAI orqali).
    Qaytaradi: 1536 o'lchamli vektor (list)
    """
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding


if __name__ == "__main__":
    # Test qilish uchun
    test_text = "Python - mashhur dasturlash tili."
    vector = get_embedding(test_text)

    print(f"Vektor o'lchami: {len(vector)}")
    print(f"Birinchi 5 ta qiymat: {vector[:5]}")