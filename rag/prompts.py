def build_rag_prompt(query, chunks, chat_history=None, selected_titles=None):
    if not chunks:
        context = "No relevant content was found in the user's documents for this question."
    else:
        parts = []
        for i, chunk in enumerate(chunks, 1):
            title = chunk.get("title") or f"Document {chunk.get('document_id')}"
            parts.append(f'[Source {i} - from "{title}"]\n{chunk["text"]}')
        context = "\n\n".join(parts)

    if selected_titles:
        scope = "The user has selected these documents: " + ", ".join(f'"{t}"' for t in selected_titles) + "."
    else:
        scope = "The user is searching across all of their uploaded documents."

    history_text = ""
    if chat_history:
        lines = []
        for msg in chat_history:
            label = "User" if msg["role"] == "user" else "Assistant"
            lines.append(f"{label}: {msg['content']}")
        history_text = "Recent conversation:\n" + "\n".join(lines) + "\n\n"

    return f"""You are a helpful assistant that answers questions using the user's uploaded documents.

{scope}
The content of those documents is already provided below under "Context". You already have access to it.

Rules:
- NEVER ask the user to select, name, choose or upload a document. Just answer from the Context.
- If the question is vague (for example "what about the document" or "tell me about it"), give a clear summary of the Context.
- Use only the Context. If the answer is not in it, say so honestly instead of guessing.
- Each source is labelled with its document. If sources come from different documents, say which document each detail comes from and never mix them up.

Context:
{context}

{history_text}User: {query}
Assistant:"""