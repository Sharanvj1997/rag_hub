from pypdf import PdfReader


def extract_text(file_path, file_type):
    """Extract raw text from a PDF or plain text file."""

    if file_type == "pdf":
        reader = PdfReader(file_path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text

    if file_type in ("txt", "md"):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    raise ValueError(f"Unsupported file type for extraction: {file_type}")


def chunk_text(text, chunk_size=1000, overlap=150):
    """
    Split text into overlapping chunks by character count.
    Overlap keeps context continuity across chunk boundaries,
    so a fact split across two chunks isn't lost entirely.
    """

    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap

    return chunks