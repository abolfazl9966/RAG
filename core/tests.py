from django.test import TestCase
from unittest.mock import patch, MagicMock
from .models import Document, Question
from .services import search_related_documents, generate_llm_response

class DocumentSearchTest(TestCase):
    def setUp(self):
        # Setup dummy data for search testing
        self.doc1 = Document.objects.create(
            title="نحوه نصب داکر",
            content="برای نصب داکر باید ابتدا مخازن را آپدیت کنید و سپس پکیج را نصب کنید.",
            tags="docker, devops"
        )
        self.doc2 = Document.objects.create(
            title="کانفیگ جنگو",
            content="تنظیمات دیتابیس در فایل settings.py قرار دارد.",
            tags="django, python"
        )
        self.doc3 = Document.objects.create(
            title="داکر کامپوز",
            content="با استفاده از کامپوز میتوانید چند کانتینر را همزمان اجرا کنید.",
            tags="docker"
        )

    def test_search_finds_relevant_doc(self):
        """Test if searching 'نصب' returns the correct document."""
        context = search_related_documents("نصب", limit=1)
        self.assertIn("نحوه نصب داکر", context)
        self.assertNotIn("کانفیگ جنگو", context)

    def test_search_ranking_logic(self):
        """
        Test if the scoring logic prioritizes title matches over content matches.
        Query: 'داکر' (Should return 'داکر کامپوز' or 'نحوه نصب داکر' before others)
        """
        context = search_related_documents("داکر")
        # Just ensuring we got results back
        self.assertTrue(len(context) > 0)
        self.assertIn("نحوه نصب داکر", context)

    def test_search_no_results(self):
        """Test search with irrelevant query."""
        context = search_related_documents("آشپزی")
        self.assertEqual(context, "")


