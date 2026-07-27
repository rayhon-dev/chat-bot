from django.contrib import admin
from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("sender", "content", "sender_user_id", "model_used", "total_tokens", "cost_usd", "created_at")
    can_delete = False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "bot", "channel", "chat_type", "external_chat_id", "started_at")
    list_filter = ("channel", "chat_type", "bot")
    search_fields = ("external_chat_id",)
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "sender", "short_content", "model_used", "total_tokens", "cost_usd", "created_at")
    list_filter = ("sender", "model_used", "created_at")
    readonly_fields = ("content",)

    @admin.display(description="Xabar")
    def short_content(self, obj):
        return obj.content[:60] + "..." if len(obj.content) > 60 else obj.content