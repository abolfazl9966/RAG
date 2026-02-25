import os
import logging
from collections import Counter
from django.db.models import Q
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from .models import Document

logger = logging.getLogger(__name__)

def search_related_documents(query_text: str, limit: int = 3) -> str:
    """
    Performs a weighted keyword search. 
    It prioritizes matches in the 'title' over 'content' to improve relevance.
    """
    if not query_text:
        return ""

    
    terms = [t.lower() for t in query_text.split() if len(t) > 2] 
    
    if not terms:
        return ""


    db_query = Q()
    for term in terms:
        db_query |= Q(title__icontains=term) | Q(content__icontains=term)
    
    candidates = Document.objects.filter(db_query).distinct()

    if not candidates.exists():
        return ""

    scored_docs = []
    
    for doc in candidates:
        score = 0
        title_lower = doc.title.lower()
        content_lower = doc.content.lower()

        for term in terms:
            if term in title_lower:
                score += 3
            score += content_lower.count(term)
        
        if score > 0:
            scored_docs.append((score, doc))

    
    scored_docs.sort(key=lambda x: x[0], reverse=True)
    top_docs = [item[1] for item in scored_docs[:limit]]

    
    context_parts = [f"Title: {d.title}\nInfo: {d.content}" for d in top_docs]
    return "\n---\n".join(context_parts)



def generate_llm_response(question: str, context: str) -> str:
    """
    Orchestrates the LLM call using LangChain.
    """
    api_key = os.getenv("OPENROUTER_API_KEY") 
    if not api_key:
        logger.error("API Key for LLM service is missing.")
        return "System configuration error: LLM provider key missing."

    if not context:
        return "متاسفانه اطلاعات کافی در اسناد موجود برای پاسخ به این سوال یافت نشد."

    try:
        llm = ChatOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            model="meta-llama/llama-3-8b-instruct",
            temperature=0.1, 
            max_tokens=512,
        )

        template = """
        You are an intelligent assistant for a documentation system.
        Answer the user's question strictly based on the provided Context.
        If the answer is not in the context, state that you don't know.
        
        Context:
        {context}
        
        User Question:
        {question}
        
        Answer (in Persian):
        """

        prompt = PromptTemplate(input_variables=["context", "question"], template=template)
        chain = prompt | llm | StrOutputParser()

        response = chain.invoke({"context": context, "question": question})
        return response.strip()

    except Exception as e:
        logger.error(f"LLM Generation failed: {str(e)}")
        return "خطایی در تولید پاسخ رخ داده است. لطفاً بعدا تلاش کنید."
