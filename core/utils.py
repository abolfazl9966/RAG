import re
from typing import List, Dict


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\u200c", " ")  # نیم‌فاصله
    text = text.replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_text_into_chunks(text: str, chunk_size: int = 900, overlap: int = 150) -> List[Dict]:
    """
    متن را با overlap به chunkهای مناسب RAG تقسیم می‌کند.
    خروجی شامل start/end هم هست.
    """
    text = normalize_text(text)

    if not text:
        return []

    if overlap >= chunk_size:
        overlap = max(0, chunk_size // 5)

    chunks = []
    start = 0
    text_len = len(text)
    chunk_index = 0

    while start < text_len:
        end = min(start + chunk_size, text_len)

        # تلاش برای شکستن روی مرز مناسب
        if end < text_len:
            preferred_breaks = [
                text.rfind("\n\n", start, end),
                text.rfind("\n", start, end),
                text.rfind(". ", start, end),
                text.rfind("؟", start, end),
                text.rfind("!", start, end),
                text.rfind("،", start, end),
                text.rfind(" ", start, end),
            ]
            best_break = max(preferred_breaks)
            if best_break > start + int(chunk_size * 0.6):
                end = best_break + 1

        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append({
                "chunk_index": chunk_index,
                "content": chunk_text,
                "char_start": start,
                "char_end": end,
            })
            chunk_index += 1

        if end >= text_len:
            break

        start = max(0, end - overlap)

    return chunks


def deduplicate_chunks_by_content(chunks: List[dict]) -> List[dict]:
    seen = set()
    result = []
    for chunk in chunks:
        key = chunk["content"].strip()
        if key and key not in seen:
            seen.add(key)
            result.append(chunk)
    return result
