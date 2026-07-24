from django.contrib import admin
from .models import Document, Chunk


class ChunkInline(admin.TabularInline):
    model = Chunk
    extra = 0
    readonly_fields = ("chunk_index", "chunk_text", "page_number", "milvus_vector_id")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "bot", "status", "chunk_count", "uploaded_at")
    list_filter = ("status", "bot")
    search_fields = ("original_filename",)
    inlines = [ChunkInline]

    def get_fields(self, request, obj=None):
        if obj is None:
            return ("bot", "file")
        return ("bot", "file", "original_filename", "status", "chunk_count", "uploaded_at")

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("original_filename", "status", "chunk_count", "uploaded_at")
        return ()

    def get_inline_instances(self, request, obj=None):
        if obj is None:
            return []
        return super().get_inline_instances(request, obj)