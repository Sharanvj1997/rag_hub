from functools import lru_cache
from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Cached so the model loads into memory once per worker process,
    not once per document — this is the expensive part.
    """
    return SentenceTransformer("all-MiniLM-L6-v2")


def generate_embeddings(text_chunks):
    """Returns a list of embedding vectors, one per input chunk."""
    model = get_embedding_model()
    embeddings = model.encode(text_chunks, show_progress_bar=False)
    return embeddings.tolist()