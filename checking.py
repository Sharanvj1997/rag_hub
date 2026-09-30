import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from rag.retrieval import retrieve_relevant_chunks

results = retrieve_relevant_chunks("What is this document about?", user_id=1)

for r in results:
    print(f"[doc {r['document_id']} chunk {r['chunk_index']}] distance={r['distance']:.3f}")
    print(r["text"][:150])
    print("---")