from pymilvus import MilvusClient

_client = None


def get_client():
    global _client
    if _client is None:
        _client = MilvusClient(uri="http://localhost:19530")
    return _client


def ensure_collection(collection_name, dimension):
    client = get_client()
    if not client.has_collection(collection_name=collection_name):
        client.create_collection(
            collection_name=collection_name,
            dimension=dimension,
            metric_type="COSINE",
        )


def insert_vectors(collection_name, entries):
    client = get_client()
    client.insert(collection_name=collection_name, data=entries)
    client.flush(collection_name=collection_name)


def search_vectors(collection_name, query_vector, top_k=10):
    client = get_client()
    return client.search(
        collection_name=collection_name,
        data=[query_vector],
        limit=top_k
    )