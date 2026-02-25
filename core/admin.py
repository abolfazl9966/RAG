from django.contrib import admin
from .models import Document, Question
from .services import search_related_documents, generate_llm_response

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'tags')
    search_fields = ('title', 'content', 'tags')
    list_filter = ('created_at',)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('user_question', 'short_answer', 'created_at')
    readonly_fields = ('generated_answer', 'retrieved_context')
    search_fields = ('user_question',)

    def short_answer(self, obj):
        if obj.generated_answer:
            return obj.generated_answer[:50] + "..."
        return "-"
    short_answer.short_description = "Generated Answer"

    def save_model(self, request, obj, form, change):
        context = search_related_documents(obj.user_question)
        obj.retrieved_context = context
        answer = generate_llm_response(obj.user_question, context)
        obj.generated_answer = answer
        super().save_model(request, obj, form, change)
