from pymilvus import MilvusClient

client = MilvusClient(uri="http://localhost:19530")


def create_collection(collection_name="docs"):
    """
    Collection yaratadi (agar mavjud bo'lmasa).
    Har bir fayl uchun alohida collection_name beriladi.
    """
    if client.has_collection(collection_name=collection_name):
        client.drop_collection(collection_name=collection_name)

    client.create_collection(
        collection_name=collection_name,
        dimension=1536
    )
    print(f"Collection '{collection_name}' yaratildi.")


def insert_chunks(chunks_with_embeddings, collection_name="docs"):
    """
    chunks_with_embeddings: list of dict, masalan:
    [{"id": 0, "vector": [...], "text": "..."}, ...]
    """
    client.insert(collection_name=collection_name, data=chunks_with_embeddings)
    client.flush(collection_name=collection_name)
    print(f"{len(chunks_with_embeddings)} ta chunk '{collection_name}' collection'ga saqlandi.")


def search(query_vector, collection_name="docs", top_k=3):
    """
    Berilgan vektor bo'yicha eng o'xshash chunklarni qidiradi.
    """
    results = client.search(
        collection_name=collection_name,
        data=[query_vector],
        limit=top_k,
        output_fields=["text"]
    )
    return results
