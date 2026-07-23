import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from clients.models import Bot
from conversations.models import Conversation, Message
from rag.services.chat import get_bot_response
from .sender import send_message, send_chat_action

logger = logging.getLogger(__name__)


def _get_active_bot(bot_id):
    return Bot.objects.filter(
        id=bot_id, telegram_enabled=True, is_active=True
    ).first()


def _parse_telegram_message(data):
    message = data.get("message")
    if not message or "text" not in message:
        return None

    chat = message.get("chat", {})
    from_user = message.get("from", {})

    return {
        "chat_id": chat.get("id"),
        "chat_type": "group" if chat.get("type") in ("group", "supergroup") else "private",
        "text": message["text"],
        "sender_user_id": str(from_user.get("id", "")),
        "message_id": message.get("message_id"),
    }


def _handle_command(bot, chat_id, text):
    command = text.strip()

    if command == "/start":
        send_message(bot.telegram_bot_token, chat_id, bot.welcome_message or "Assalomu alaykum!")
        return True

    if command == "/help":
        send_message(bot.telegram_bot_token, chat_id, "Savolingizni yozing, men javob beraman.")
        return True

    return False


def _get_or_create_conversation(bot, chat_id, chat_type):
    conversation, _ = Conversation.objects.get_or_create(
        bot=bot,
        channel=Conversation.Channel.TELEGRAM,
        external_chat_id=str(chat_id),
        defaults={"chat_type": chat_type},
    )
    return conversation


@csrf_exempt
@require_POST
def telegram_webhook(request, bot_id):
    bot = _get_active_bot(bot_id)
    if not bot:
        logger.warning(f"Webhook chaqirildi, lekin bot topilmadi: bot_id={bot_id}")
        return JsonResponse({"ok": False}, status=404)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        logger.warning("Telegram'dan noto'g'ri JSON keldi")
        return JsonResponse({"ok": False}, status=400)

    parsed = _parse_telegram_message(data)
    if not parsed:
        return JsonResponse({"ok": True})

    chat_id = parsed["chat_id"]
    chat_type = parsed["chat_type"]
    text = parsed["text"]
    message_id = parsed["message_id"]

    if chat_type == "group" and not bot.telegram_group_mode:
        return JsonResponse({"ok": True})

    if _handle_command(bot, chat_id, text):
        return JsonResponse({"ok": True})

    conversation = _get_or_create_conversation(bot, chat_id, chat_type)

    Message.objects.create(
        conversation=conversation,
        sender=Message.Sender.USER,
        content=text,
        sender_user_id=parsed["sender_user_id"],
    )

    send_chat_action(bot.telegram_bot_token, chat_id, "typing")

    criteria = bot.relevance_criteria if chat_type == "group" else None

    try:
        answer = get_bot_response(bot, text, relevance_criteria=criteria)
    except Exception as e:
        logger.exception(f"Bot javob berishda xato (bot_id={bot_id}): {e}")
        answer = bot.fallback_message or "Kechirasiz, xatolik yuz berdi."

    if answer is None:
        return JsonResponse({"ok": True})

    Message.objects.create(
        conversation=conversation,
        sender=Message.Sender.BOT,
        content=answer,
    )

    reply_id = message_id if chat_type == "group" else None
    send_message(bot.telegram_bot_token, chat_id, answer, reply_to_message_id=reply_id)

    return JsonResponse({"ok": True})