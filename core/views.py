import json
import logging

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View

from .models import Question
from .services import (
    search_related_documents,
    generate_llm_response,
    create_document_with_chunks,
)
from .faiss_service import rebuild_faiss_index

logger = logging.getLogger(__name__)


def chat_page(request):
    return render(request, "ragapp/chat.html")
def ingest_page(request):
    return render(request, "ragapp/ingest.html")

@method_decorator(csrf_exempt, name='dispatch')
class AskQuestionAPI(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            user_question = data.get("question", "").strip()

            if not user_question:
                return JsonResponse({"error": "Question is required"}, status=400)

            context = search_related_documents(user_question, limit=6, final_top_n=4)
            answer = generate_llm_response(user_question, context)

            question_obj = Question.objects.create(
                user_question=user_question,
                generated_answer=answer,
                retrieved_context=context
            )

            return JsonResponse({
                "id": question_obj.id,
                "question": user_question,
                "answer": answer,
                "context_used": context
            }, status=200)

        except Exception as e:
            logger.exception("AskQuestionAPI failed")
            return JsonResponse({"error": str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AddDocumentAPI(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            title = data.get("title", "").strip()
            content = data.get("content", "").strip()
            tags = data.get("tags", "").strip()

            if not title:
                return JsonResponse({"error": "Title is required"}, status=400)

            if not content:
                return JsonResponse({"error": "Content is required"}, status=400)

            document = create_document_with_chunks(
                title=title,
                content=content,
                tags=tags
            )

            return JsonResponse({
                "message": "Document added successfully",
                "document_id": document.id,
                "title": document.title,
                "chunks_count": document.chunks.count()
            }, status=201)

        except Exception as e:
            logger.exception("AddDocumentAPI failed")
            return JsonResponse({"error": str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class RebuildFaissAPI(View):
    def post(self, request):
        try:
            result = rebuild_faiss_index()
            return JsonResponse({
                "message": "FAISS index rebuilt",
                "result": result
            }, status=200)
        except Exception as e:
            logger.exception("RebuildFaissAPI failed")
            return JsonResponse({"error": str(e)}, status=500)
