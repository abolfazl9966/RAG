from django.db import models

class Document(models.Model):
    
    title = models.CharField(max_length=255)
    content = models.TextField()
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    
    user_question = models.TextField()
    generated_answer = models.TextField(blank=True, null=True)
    retrieved_context = models.TextField(blank=True, null=True, help_text="Context used by LLM")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user_question[:50]
