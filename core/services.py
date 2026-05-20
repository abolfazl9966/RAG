import os
import logging
from typing import List

from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from .models import Document, DocumentChunk
from .utils import split_text_into_chunks, deduplicate_chunks_by_content, normalize_text
from .faiss_service import rebuild_faiss_index, search_faiss

logger = logging.getLogger(__name__)

client = OpenAI(
    base_url="https://api.gapgpt.app/v1",
    api_key=os.getenv("GAPGPT_API_KEY")
)


def get_embedding(text: str) -> List[float]:
    text = normalize_text(text)
    if not text:
        return []

    emb = client.embeddings.create(
        model="text-embedding-3-large",
        input=text
    )
    return emb.data[0].embedding


def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    cleaned_texts = [normalize_text(t) for t in texts if normalize_text(t)]
    if not cleaned_texts:
        return []

    emb = client.embeddings.create(
        model="text-embedding-3-large",
        input=cleaned_texts
    )
    return [item.embedding for item in emb.data]


def create_document_with_chunks(title: str, content: str, tags: str = "") -> Document:
    """
    یک سند را ذخیره می‌کند، chunk می‌کند، embedding می‌سازد و FAISS را rebuild می‌کند.
    """
    content = normalize_text(content)
    if not content:
        raise ValueError("Document content is empty.")

    document = Document.objects.create(
        title=title.strip(),
        content=content,
        tags=tags.strip() if tags else ""
    )

    raw_chunks = split_text_into_chunks(content, chunk_size=900, overlap=150)
    raw_chunks = deduplicate_chunks_by_content(raw_chunks)

    if not raw_chunks:
        raise ValueError("No chunks generated from document.")

    chunk_texts = [chunk["content"] for chunk in raw_chunks]
    embeddings = get_embeddings_batch(chunk_texts)

    chunk_objects = []
    for chunk_data, emb in zip(raw_chunks, embeddings):
        chunk_objects.append(
            DocumentChunk(
                document=document,
                chunk_index=chunk_data["chunk_index"],
                content=chunk_data["content"],
                embedding=emb,
                char_start=chunk_data["char_start"],
                char_end=chunk_data["char_end"],
            )
        )

    DocumentChunk.objects.bulk_create(chunk_objects)
    rebuild_faiss_index()

    return document


def rebuild_document_chunks(document_id: int):
    """
    اگر سندی ویرایش شد، chunkها و embeddingهایش دوباره ساخته می‌شود.
    """
    document = Document.objects.get(id=document_id)

    DocumentChunk.objects.filter(document=document).delete()

    raw_chunks = split_text_into_chunks(document.content, chunk_size=900, overlap=150)
    raw_chunks = deduplicate_chunks_by_content(raw_chunks)
    chunk_texts = [chunk["content"] for chunk in raw_chunks]
    embeddings = get_embeddings_batch(chunk_texts)

    chunk_objects = []
    for chunk_data, emb in zip(raw_chunks, embeddings):
        chunk_objects.append(
            DocumentChunk(
                document=document,
                chunk_index=chunk_data["chunk_index"],
                content=chunk_data["content"],
                embedding=emb,
                char_start=chunk_data["char_start"],
                char_end=chunk_data["char_end"],
            )
        )

    DocumentChunk.objects.bulk_create(chunk_objects)
    rebuild_faiss_index()
    return document


def lexical_score(query: str, text: str) -> int:
    query_words = set(normalize_text(query).lower().split())
    text_words = set(normalize_text(text).lower().split())
    if not query_words or not text_words:
        return 0
    return len(query_words.intersection(text_words))


def rerank_chunks(question: str, chunks, top_n=4):
    """
    ترکیب semantic retrieval + lexical overlap برای دقت بیشتر
    """
    scored = []
    for chunk in chunks:
        score = lexical_score(question, chunk.content)
        scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)

    reranked = [item[1] for item in scored[:top_n]]

    # اگر lexical چیزی تشخیص نداد، همان اولی‌ها را بده
    if not reranked:
        return list(chunks)[:top_n]

    return reranked


def search_related_documents(query_text: str, limit: int = 6, final_top_n: int = 4, context_window: int = 1) -> str:
    """
    مرحله retrieval:
    1) embedding query
    2) faiss search
    3) rerank
    4) برای هر chunk، چانک‌های قبل و بعد را هم بیاور
    5) ساخت context نهایی
    
    context_window: تعداد چانک‌های قبل و بعد (پیش‌فرض 1)
    """
    if not query_text:
        return ""

    try:
        query_embedding = get_embedding(query_text)
        if not query_embedding:
            return ""

        candidate_chunks = search_faiss(query_embedding, k=limit)
        if not candidate_chunks:
            return ""

        selected_chunks = rerank_chunks(query_text, candidate_chunks, top_n=final_top_n)

        # برای هر chunk، چانک‌های مجاور را پیدا کن
        expanded_chunks = []
        seen = set()

        for chunk in selected_chunks:
            # محدوده چانک‌های مورد نیاز
            start_index = max(0, chunk.chunk_index - context_window)
            end_index = chunk.chunk_index + context_window + 1

            # بیاوردن چانک‌های مجاور از همان document
            neighbor_chunks = DocumentChunk.objects.filter(
                document_id=chunk.document_id,
                chunk_index__gte=start_index,
                chunk_index__lt=end_index
            ).select_related("document").order_by("chunk_index")

            for nc in neighbor_chunks:
                key = (nc.document_id, nc.chunk_index)
                if key not in seen:
                    seen.add(key)
                    expanded_chunks.append(nc)

        # مرتب‌سازی بر اساس document و chunk_index
        expanded_chunks.sort(key=lambda x: (x.document_id, x.chunk_index))

        # ساخت context
        context_parts = []
        current_doc_id = None
        current_doc_chunks = []

        for chunk in expanded_chunks:
            if current_doc_id != chunk.document_id:
                # اگر document عوض شد، قبلی را اضافه کن
                if current_doc_chunks:
                    merged_content = "\n".join([c.content for c in current_doc_chunks])
                    context_parts.append(
                        f"عنوان سند: {current_doc_chunks[0].document.title}\n"
                        f"بخش‌های {current_doc_chunks[0].chunk_index} تا {current_doc_chunks[-1].chunk_index}:\n"
                        f"{merged_content}"
                    )
                
                current_doc_id = chunk.document_id
                current_doc_chunks = [chunk]
            else:
                current_doc_chunks.append(chunk)

        # آخرین document را هم اضافه کن
        if current_doc_chunks:
            merged_content = "\n".join([c.content for c in current_doc_chunks])
            context_parts.append(
                f"عنوان سند: {current_doc_chunks[0].document.title}\n"
                f"بخش‌های {current_doc_chunks[0].chunk_index} تا {current_doc_chunks[-1].chunk_index}:\n"
                f"{merged_content}"
            )

        return "\n\n---\n\n".join(context_parts)

    except Exception as e:
        logger.exception(f"Semantic retrieval failed: {e}")
        return ""



def generate_llm_response(question: str, context: str) -> str:
    """
    پاسخ دقیق با محدود شدن کامل به context
    """
    api_key = os.getenv("GAPGPT_API_KEY")
    if not api_key:
        logger.error("API Key for LLM service is missing.")
        return "خطا: API Key تنظیم نشده است."

    if not context:
        return "نمی‌دانم."

    try:
        llm = ChatOpenAI(
            api_key=api_key,
            base_url="https://api.gapgpt.app/v1",
            model="gpt-5.2",
            temperature=0,
            max_tokens=2000,
            timeout=30,
        )

        template = """
شما یک دستیار پاسخ‌گوی دقیق هستید.
فقط و فقط بر اساس CONTEXT جواب بده.
اگر پاسخ به طور مستقیم یا با اطمینان کافی در متن پیدا نشد، فقط بنویس:
نمی‌دانم.

قوانین:
- از اطلاعات بیرون از متن استفاده نکن.
- جواب را دقیق، شفاف و فارسی بنویس.
- اگر لازم بود، پاسخ را در 2 تا 8 جمله بده.
- اگر سوال چندبخشی است، فقط بخش‌هایی را پاسخ بده که در متن آمده‌اند.
- از حدس زدن خودداری کن.

CONTEXT:
{context}

QUESTION:
{question}

پاسخ:
"""

        prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=template
        )

        chain = prompt | llm | StrOutputParser()
        response = chain.invoke({
            "context": context,
            "question": question
        })

        response = response.strip()
        return response if response else "نمی‌دانم."

    except Exception as e:
        logger.exception(f"LLM error: {e}")
        return "خطایی رخ داد. بعداً دوباره تلاش کنید."
