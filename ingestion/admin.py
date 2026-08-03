from django.contrib import admin, messages
from .models import Document, Chunk


# admin.py faylingizdagi ChunkInline qismini shunday o'zgartiring:

class ChunkInline(admin.TabularInline):
    model = Chunk
    extra = 0
    show_change_link = True
    readonly_fields = ("chunk_index", "chunk_text", "page_number", "milvus_vector_id")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs[:30]


def _set_document_language(modeladmin, request, queryset, lang_code, lang_name):
    updated = queryset.update(language=lang_code)
    modeladmin.message_user(
        request,
        f"{updated} ta hujjat tili '{lang_name}' ga oʻzgartirildi.",
        messages.SUCCESS
    )


@admin.action(description="Tanlanganlarni Oʻzbekcha (uz) qilish")
def set_lang_uz(modeladmin, request, queryset):
    _set_document_language(modeladmin, request, queryset, 'uz', 'Oʻzbekcha')


@admin.action(description="Tanlanganlarni Русский (ru) qilish")
def set_lang_ru(modeladmin, request, queryset):
    _set_document_language(modeladmin, request, queryset, 'ru', 'Русский')


@admin.action(description="Tanlanganlarni English (en) qilish")
def set_lang_en(modeladmin, request, queryset):
    _set_document_language(modeladmin, request, queryset, 'en', 'English')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "bot", "language", "status", "chunk_count", "uploaded_at")
    list_filter = ("status", "bot", "language")
    search_fields = ("original_filename",)

    actions = [set_lang_uz, set_lang_ru, set_lang_en]

    inlines = [ChunkInline]

    def get_fields(self, request, obj=None):
        if obj is None:
            return ("bot", "file", "language")
        return ("bot", "file", "original_filename", "language", "status", "chunk_count", "uploaded_at")

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("original_filename", "status", "chunk_count", "uploaded_at")
        return ()

    def get_inline_instances(self, request, obj=None):
        if obj is None:
            return []
        return super().get_inline_instances(request, obj)