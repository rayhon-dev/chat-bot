import logging

from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver

from .models import Document
from .services.pipeline import process_document
from rag.services.milvus_client import delete_vectors

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Document)
def trigger_processing_on_upload(sender, instance, created, **kwargs):
    if created and instance.status == "pending":
        try:
            process_document(instance)
        except Exception:
            logger.exception(f"Hujjatni qayta ishlashda xato (document_id={instance.id})")


@receiver(pre_delete, sender=Document)
def _capture_vectors_before_delete(sender, instance, **kwargs):
    instance._milvus_collection_name = instance.bot.milvus_collection_name
    instance._milvus_vector_ids = list(
        instance.chunks.exclude(milvus_vector_id="").values_list("milvus_vector_id", flat=True)
    )


@receiver(post_delete, sender=Document)
def _cleanup_vectors_after_delete(sender, instance, **kwargs):
    collection_name = getattr(instance, "_milvus_collection_name", None)
    vector_ids = getattr(instance, "_milvus_vector_ids", None)
    if not collection_name or not vector_ids:
        return
    try:
        delete_vectors(collection_name, [int(v) for v in vector_ids])
    except Exception:
        logger.exception(f"Milvus vektorlarni o'chirishda xato (document_id={instance.id})")