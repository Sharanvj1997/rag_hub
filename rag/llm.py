import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"


def generate_response(prompt, stream=False):
    """
    Sends a prompt to the local Ollama model.

    stream=False: returns the full response as a string (used for testing).
    stream=True: returns a generator yielding tokens as they arrive
                 (used later for the SSE chat endpoint).
    """

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": stream,
    }

    if not stream:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")

    # Streaming mode: Ollama sends newline-delimited JSON objects,
    # one per token/chunk, as the response streams in.
    response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=120)
    response.raise_for_status()

    def token_generator():
        for line in response.iter_lines():
            if not line:
                continue
            chunk = json.loads(line.decode("utf-8"))
            if "response" in chunk:
                yield chunk["response"]
            if chunk.get("done"):
                break

    return token_generator()