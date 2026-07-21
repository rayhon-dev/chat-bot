from django.contrib import admin
from django.contrib import messages
from .models import Document, Chunk
from .services.pipeline import process_document


class ChunkInline(admin.TabularInline):
    model = Chunk
    extra = 0
    readonly_fields = ['chunk_text', 'chunk_index', 'page_number', 'milvus_vector_id']
    can_delete = False


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    exclude = ['original_filename']
    list_display = ['original_filename', 'bot', 'status', 'uploaded_at']
    readonly_fields = ['status']
    inlines = [ChunkInline]
    actions = ['process_selected_documents']

    @admin.action(description="Tanlangan fayllarni qayta ishlash (Process)")
    def process_selected_documents(self, request, queryset):
        success_count = 0
        for document in queryset:
            try:
                process_document(document)
                success_count += 1
            except Exception as e:
                self.message_user(
                    request,
                    f"'{document.original_filename}' xato: {e}",
                    level=messages.ERROR
                )
        if success_count:
            self.message_user(request, f"{success_count} ta fayl muvaffaqiyatli qayta ishlandi.")