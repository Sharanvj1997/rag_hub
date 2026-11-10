from .embeddings import generate_embeddings
from .vectorstore import get_collection

# If the selected scope has this many chunks or fewer, send ALL of them to the LLM
# instead of ranking by similarity. Small documents (resumes, profiles) are then
# answered from the whole document, even for vague questions like "summarize it".
FULL_CONTEXT_LIMIT = 8


def _build_where(user_id, document_ids=None):
    # user_id is ALWAYS part of the filter, so a document filter can never widen access
    if document_ids:
        return {"$and": [
            {"user_id": user_id},
            {"document_id": {"$in": list(document_ids)}},
        ]}
    return {"user_id": user_id}


def retrieve_relevant_chunks(query, user_id, top_k=6, document_ids=None):
    collection = get_collection()
    where = _build_where(user_id, document_ids)

    stored = collection.get(where=where, include=["documents", "metadatas"])
    total = len(stored["ids"])

    if total == 0:
        return []

    # Small scope: use everything, in reading order
    if total <= FULL_CONTEXT_LIMIT:
        items = sorted(
            zip(stored["documents"], stored["metadatas"]),
            key=lambda pair: (pair[1]["document_id"], pair[1]["chunk_index"]),
        )
        return [
            {
                "text": text,
                "document_id": meta["document_id"],
                "chunk_index": meta["chunk_index"],
                "distance": None,
            }
            for text, meta in items
        ]

    # Larger scope: similarity search (top_k is clamped to avoid the ChromaDB bug)
    query_embedding = generate_embeddings([query])[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, total),
        where=where,
    )

    chunks = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for text, meta, distance in zip(documents, metadatas, distances):
        chunks.append({
            "text": text,
            "document_id": meta.get("document_id"),
            "chunk_index": meta.get("chunk_index"),
            "distance": distance,
        })
    return chunks