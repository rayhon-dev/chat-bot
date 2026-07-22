from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Document
from .services.pipeline import process_document


@receiver(post_save, sender=Document)
def trigger_processing_on_upload(sender, instance, created, **kwargs):
    if created and instance.status == "pending":
        process_document(instance)