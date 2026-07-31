from celery import shared_task
from .models import Document


@shared_task
def process_document_task(document_id):
    from .services.pipeline import process_document
    document = Document.objects.get(id=document_id)
    process_document(document)