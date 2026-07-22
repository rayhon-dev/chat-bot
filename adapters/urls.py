from django.urls import path
from .telegram import webhook
from .website import widget_api

urlpatterns = [
    path('telegram/webhook/<int:bot_id>/', webhook.telegram_webhook, name='telegram_webhook'),
    path('chat/', widget_api.chat_endpoint, name='chat_endpoint'),
]