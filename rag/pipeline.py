from .chunking import extract_text, chunk_text
from .embeddings import generate_embeddings
from .vectorstore import store_chunks


def process_document(document):
    """
    Full ingestion pipeline: extract -> chunk -> embed -> store.
    Raises on failure so the caller (Celery task) can catch it
    and set status=failed with the error message.
    """

    text = extract_text(document.file.path, document.file_type)

    if not text.strip():
        raise ValueError("No extractable text found in this document.")

    chunks = chunk_text(text)

    if not chunks:
        raise ValueError("Document produced no chunks after splitting.")

    embeddings = generate_embeddings(chunks)

    store_chunks(
        document_id=document.id,
        user_id=document.owner_id,
        chunks=chunks,
        embeddings=embeddings,
    )

    return len(chunks)