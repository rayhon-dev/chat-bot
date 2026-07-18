from pymilvus import MilvusClient

# Local fayl sifatida Milvus (Docker kerak emas)
client = MilvusClient("chatbot.db")

COLLECTION_NAME = "docs"


def create_collection():
    """
    Collection yaratadi (agar mavjud bo'lmasa).
    dimension=1536 chunki OpenAI text-embedding-3-small shu o'lchamni beradi.
    """
    if client.has_collection(collection_name=COLLECTION_NAME):
        client.drop_collection(collection_name=COLLECTION_NAME)  # test uchun, har safar tozalab boshlaymiz

    client.create_collection(
        collection_name=COLLECTION_NAME,
        dimension=1536
    )
    print(f"Collection '{COLLECTION_NAME}' yaratildi.")


def insert_chunks(chunks_with_embeddings):
    """
    chunks_with_embeddings: list of dict, masalan:
    [{"id": 0, "vector": [...], "text": "..."}, ...]
    """
    client.insert(collection_name=COLLECTION_NAME, data=chunks_with_embeddings)
    print(f"{len(chunks_with_embeddings)} ta chunk Milvus'ga saqlandi.")


def search(query_vector, top_k=3):
    """
    Berilgan vektor bo'yicha eng o'xshash chunklarni qidiradi.
    """
    results = client.search(
        collection_name=COLLECTION_NAME,
        data=[query_vector],
        limit=top_k,
        output_fields=["text"]
    )
    return results


if __name__ == "__main__":
    create_collection()