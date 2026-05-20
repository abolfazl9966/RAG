from django.core.management.base import BaseCommand
from core.faiss_service import rebuild_faiss_index


class Command(BaseCommand):
    help = "Rebuild FAISS index from document chunks"

    def handle(self, *args, **options):
        result = rebuild_faiss_index()
        self.stdout.write(self.style.SUCCESS(f"FAISS rebuild result: {result}"))
