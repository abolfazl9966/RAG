from django.contrib import admin
from .models import Document, DocumentChunk, Question


class DocumentChunkInline(admin.TabularInline):
    model = DocumentChunk
    extra = 0
    readonly_fields = ("chunk_index", "char_start", "char_end", "created_at")
    fields = ("chunk_index", "content", "char_start", "char_end", "created_at")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "tags", "created_at")
    search_fields = ("title", "content", "tags")
    inlines = [DocumentChunkInline]


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ("id", "document", "chunk_index", "char_start", "char_end", "created_at")
    search_fields = ("content", "document__title")
    list_filter = ("document",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "short_question", "created_at")
    search_fields = ("user_question", "generated_answer", "retrieved_context")

    def short_question(self, obj):
        return obj.user_question[:80]
    short_question.short_description = "Question"
