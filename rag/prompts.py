def build_rag_prompt(query, chunks, chat_history=None):
    """
    Builds a prompt combining retrieved context with the user's question.
    chat_history: optional list of {"role": "user"/"assistant", "content": ...}
    """

    if not chunks:
        context = "No relevant documents were found for this question."
    else:
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"[Source {i}]\n{chunk['text']}")
        context = "\n\n".join(context_parts)

    history_text = ""
    if chat_history:
        history_lines = []
        for msg in chat_history:
            role_label = "User" if msg["role"] == "user" else "Assistant"
            history_lines.append(f"{role_label}: {msg['content']}")
        history_text = "\n".join(history_lines) + "\n\n"

    prompt = f"""You are a helpful assistant answering questions based on the user's uploaded documents.
Use only the information in the context below to answer. If the answer isn't in the context, say so honestly rather than making something up.

Context from documents:
{context}

{history_text}User: {query}
Assistant:"""

    return prompt