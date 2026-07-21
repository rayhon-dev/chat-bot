import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from clients.models import Bot
from conversations.models import Conversation, Message
from rag.services.chat import get_bot_response
from .sender import send_message, send_chat_action


@csrf_exempt
@require_POST
def telegram_webhook(request, bot_id):
    try:
        bot = Bot.objects.get(id=bot_id, telegram_enabled=True, is_active=True)
    except Bot.DoesNotExist:
        return JsonResponse({"ok": False}, status=404)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False}, status=400)

    message = data.get("message")
    if not message:
        return JsonResponse({"ok": True})

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    chat_type_raw = chat.get("type")
    chat_type = "group" if chat_type_raw in ("group", "supergroup") else "private"
    text = message.get("text", "")
    from_user = message.get("from", {})
    sender_user_id = str(from_user.get("id", ""))

    if not text:
        return JsonResponse({"ok": True})

    # Maxsus komandalarni ishlash
    if text.strip() == "/start":
        send_message(bot.telegram_bot_token, chat_id, bot.welcome_message or "Assalomu alaykum!")
        return JsonResponse({"ok": True})

    if text.strip() == "/help":
        send_message(bot.telegram_bot_token, chat_id, "Savolingizni yozing, men javob beraman.")
        return JsonResponse({"ok": True})

    # Guruhda faqat mention/reply bo'lsa javob berish (agar group_mode yoqilgan bo'lsa)
    if chat_type == "group" and not bot.telegram_group_mode:
        return JsonResponse({"ok": True})

    # Conversation topish yoki yaratish
    conversation, _ = Conversation.objects.get_or_create(
        bot=bot,
        channel=Conversation.Channel.TELEGRAM,
        external_chat_id=str(chat_id),
        defaults={"chat_type": chat_type},
    )

    Message.objects.create(
        conversation=conversation,
        sender=Message.Sender.USER,
        content=text,
        sender_user_id=sender_user_id,
    )

    send_chat_action(bot.telegram_bot_token, chat_id, "typing")

    try:
        answer = get_bot_response(bot, text)
    except Exception as e:
        answer = bot.fallback_message or "Kechirasiz, xatolik yuz berdi."

    Message.objects.create(
        conversation=conversation,
        sender=Message.Sender.BOT,
        content=answer,
    )

    # Uzun javobni bo'lib yuborish (Telegram 4096 belgi limiti)
    for i in range(0, len(answer), 4000):
        send_message(bot.telegram_bot_token, chat_id, answer[i:i + 4000])

    return JsonResponse({"ok": True})