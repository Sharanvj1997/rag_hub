import chromadb
from django.conf import settings

_client = None


def get_chroma_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=str(settings.BASE_DIR / "chroma_data")
        )
    return _client


def get_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(name="documents")


def store_chunks(document_id, user_id, chunks, embeddings):
    """
    Stores chunks with user_id in metadata — this is the multi-tenant
    filter every retrieval query must use later.
    """
    collection = get_collection()

    ids = [f"doc{document_id}_chunk{i}" for i in range(len(chunks))]
    metadatas = [
        {"document_id": document_id, "user_id": user_id, "chunk_index": i}
        for i in range(len(chunks))
    ]

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )


def delete_document_chunks(document_id):
    """Called when a document is deleted, so orphaned vectors don't linger."""
    collection = get_collection()
    collection.delete(where={"document_id": document_id})