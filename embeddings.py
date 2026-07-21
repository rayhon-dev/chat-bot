# import os
# from dotenv import load_dotenv
# from openai import OpenAI
#
# load_dotenv()
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#
#
# def get_embedding(text):
#     response = client.embeddings.create(
#         input=text,
#         model="text-embedding-3-small"
#     )
#     return response.data[0].embedding
#
#
# def translate_to_english(text):
#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[
#             {"role": "system", "content": "Translate the following text to English. Only return the translation, nothing else, no explanations."},
#             {"role": "user", "content": text}
#         ]
#     )
#     return response.choices[0].message.content
#
#
#
# def get_embeddings_batch(texts, batch_size=100):
#     all_embeddings = []
#     for i in range(0, len(texts), batch_size):
#         batch = texts[i:i + batch_size]
#         response = client.embeddings.create(
#             input=batch,
#             model="text-embedding-3-small"
#         )
#         batch_embeddings = [item.embedding for item in response.data]
#         all_embeddings.extend(batch_embeddings)
#         print(f"Batch {i // batch_size + 1}: {len(batch)} ta chunk embedding qilindi")
#     return all_embeddings
#
