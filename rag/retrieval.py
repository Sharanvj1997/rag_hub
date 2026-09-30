from .embeddings import generate_embeddings
from .vectorstore import get_collection


def retrieve_relevant_chunks(query, user_id, top_k=4):
    query_embedding = generate_embeddings([query])[0]

    collection = get_collection()

    # Clamp top_k to avoid a ChromaDB internal error when the filtered
    # subset has fewer items than requested.
    available = collection.get(where={"user_id": user_id}, include=[])
    available_count = len(available["ids"])

    if available_count == 0:
        return []

    safe_top_k = min(top_k, available_count)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=safe_top_k,
        where={"user_id": user_id},
    )

    chunks = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc_text, metadata, distance in zip(documents, metadatas, distances):
        chunks.append({
            "text": doc_text,
            "document_id": metadata.get("document_id"),
            "chunk_index": metadata.get("chunk_index"),
            "distance": distance,
        })

    return chunks