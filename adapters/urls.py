from django.urls import path
from .telegram.webhook import telegram_webhook

urlpatterns = [
    path("telegram/webhook/<int:bot_id>/", telegram_webhook, name="telegram_webhook"),
]