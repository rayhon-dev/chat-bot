from django.db import models
from clients.models import Bot
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex


class Document(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Kutilmoqda"
        PROCESSING = "processing", "Qayta ishlanmoqda"
        READY = "ready", "Tayyor"
        FAILED = "failed", "Xato"

    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('uz', 'Oʻzbekcha'),
        ('ru', 'Русский'),
    ]

    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name="documents")
    file = models.FileField(upload_to="uploads/")
    original_filename = models.CharField(max_length=255, blank=True)
    language = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default='en',
        help_text="Botga yuklangan hujjatlar va javoblar tili"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    chunk_count = models.IntegerField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)


    def save(self, *args, **kwargs):
        if not self.original_filename and self.file:
            self.original_filename = self.file.name
        super().save(*args, **kwargs)


class Chunk(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    chunk_text = models.TextField()
    chunk_index = models.IntegerField()
    page_number = models.IntegerField(blank=True, null=True)
    milvus_vector_id = models.CharField(max_length=255)
    search_vector = SearchVectorField(null=True, blank=True)

    class Meta:
        indexes = [GinIndex(fields=["search_vector"])]

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.original_filename}"