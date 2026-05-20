from django.urls import path
from .views import (
    chat_page,
    ingest_page,
    AskQuestionAPI,
    AddDocumentAPI,
    RebuildFaissAPI,
)

urlpatterns = [
    path("", chat_page, name="chat_page"),
    path("ingest/", ingest_page, name="ingest_page"),

    path("ask/", AskQuestionAPI.as_view(), name="ask_question"),
    path("documents/add/", AddDocumentAPI.as_view(), name="add_document"),
    path("faiss/rebuild/", RebuildFaissAPI.as_view(), name="rebuild_faiss"),
]
