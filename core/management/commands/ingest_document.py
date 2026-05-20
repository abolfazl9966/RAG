from django.core.management.base import BaseCommand, CommandError
from core.services import create_document_with_chunks


class Command(BaseCommand):
    help = "Ingest a document from a text file into the RAG system"

    def add_arguments(self, parser):
        parser.add_argument("--title", type=str, required=True, help="Document title")
        parser.add_argument("--file", type=str, required=True, help="Path to text file")
        parser.add_argument("--tags", type=str, default="", help="Optional tags")

    def handle(self, *args, **options):
        title = options["title"]
        file_path = options["file"]
        tags = options["tags"]

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            raise CommandError("File not found")

        document = create_document_with_chunks(
            title=title,
            content=content,
            tags=tags
        )

        self.stdout.write(self.style.SUCCESS(
            f"Document ingested successfully. ID={document.id}, chunks={document.chunks.count()}"
        ))
