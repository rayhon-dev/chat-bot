from django.contrib import admin
from .models import Client, Bot


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "contact_email", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "contact_email")


@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "client", "is_active", "telegram_enabled", "website_enabled", "uses_rag", "llm_provider")
    list_filter = ("is_active", "telegram_enabled", "website_enabled", "uses_rag", "llm_provider")
    search_fields = ("name", "slug", "client__name")
    fieldsets = (
        ("Asosiy", {"fields": ("client", "name", "slug", "is_active")}),
        ("Telegram", {"fields": ("telegram_enabled", "telegram_bot_token", "telegram_group_mode")}),
        ("Website", {"fields": ("website_enabled", "api_key")}),
        ("RAG va LLM", {"fields": (
            "uses_rag", "api_key_source", "llm_provider", "llm_model",
            "embedding_model", "milvus_collection_name", "temperature",
        )}),
        ("Xulq-atvor", {"fields": ("system_prompt", "welcome_message", "fallback_message", "relevance_criteria")}),
    )