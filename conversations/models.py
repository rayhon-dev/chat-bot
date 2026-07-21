from django.db import models
from clients.models import Bot


class Conversation(models.Model):
    class Channel(models.TextChoices):
        TELEGRAM = "telegram", "Telegram"
        WEBSITE = "website", "Website"

    class ChatType(models.TextChoices):
        PRIVATE = "private", "Shaxsiy"
        GROUP = "group", "Guruh"

    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name="conversations")
    channel = models.CharField(max_length=20, choices=Channel.choices)
    chat_type = models.CharField(max_length=20, choices=ChatType.choices, default=ChatType.PRIVATE)
    external_chat_id = models.CharField(max_length=255)
    started_at = models.DateTimeField(auto_now_add=True)


class Message(models.Model):
    class Sender(models.TextChoices):
        USER = "user", "Foydalanuvchi"
        BOT = "bot", "Bot"

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=10, choices=Sender.choices)
    content = models.TextField()
    sender_user_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)