from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
from .models import Question
from .services import search_related_documents, generate_llm_response

@method_decorator(csrf_exempt, name='dispatch')
class AskQuestionAPI(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            user_question = data.get('question')
            
            if not user_question:
                return JsonResponse({'error': 'Question is required'}, status=400)

            # create question object
            question_obj = Question(user_question=user_question)
            
            #find related documents
            context = search_related_documents(user_question)
            question_obj.retrieved_context = context
            #generate answer
            answer = generate_llm_response(user_question, context)
            question_obj.generated_answer = answer
            
            question_obj.save()

            return JsonResponse({
                'question': user_question,
                'answer': answer,
                'context_used': context
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
