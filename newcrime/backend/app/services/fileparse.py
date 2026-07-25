"""Document text extraction and entity recognition (stub).

extract_entities is not implemented — it returns empty lists. Callers must not
present its output as analysis.
"""
from __future__ import annotations

SUPPORTED_MIMES = {"application/pdf", "text/plain", "text/csv",
                   "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}

# what we can actually turn into text without a parsing library
_TEXT_MIMES = {"text/plain", "text/csv", "text/markdown", "application/json"}


def is_supported(mime: str) -> bool:
    return mime in SUPPORTED_MIMES


def extract_text(path: str, mime: str = "") -> str:
    try:
        with open(path, "rb") as f:
            return extract_text_from_bytes(f.read(), mime)
    except Exception:
        return ""


def extract_text_from_bytes(data: bytes, mime: str = "") -> str:
    """Best-effort text from raw bytes.

    Returns "" for formats needing a real parser (PDF, DOCX) rather than
    emitting binary noise that would poison a summary.
    """
    if not data:
        return ""
    if mime and mime not in _TEXT_MIMES and not mime.startswith("text/"):
        return ""
    try:
        text = data.decode("utf-8", errors="replace")
    except Exception:
        return ""
    # a decoded binary blob is mostly replacement chars — treat as unparseable
    if text.count("�") > len(text) * 0.1:
        return ""
    return text[:5000]


def extract_entities(text: str) -> dict:
    return {"persons": [], "locations": [], "dates": [], "amounts": []}
