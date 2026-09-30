import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from functools import lru_cache
from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)
def get_embedding_model():
    return SentenceTransformer("all-MiniLM-L6-v2")


def generate_embeddings(text_chunks):
    model = get_embedding_model()
    embeddings = model.encode(text_chunks, show_progress_bar=False)
    return embeddings.tolist()