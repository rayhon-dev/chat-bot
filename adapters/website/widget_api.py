import logging
import uuid

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from clients.models import Bot
from conversations.models import Conversation, Message
from rag.services.chat import get_bot_response

logger = logging.getLogger(__name__)


@api_view(['POST'])
def chat_endpoint(request):
    api_key = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not api_key:
        return Response({"error": "API key kerak"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        bot = Bot.objects.get(api_key=api_key, is_active=True, website_enabled=True)
    except Bot.DoesNotExist:
        return Response({"error": "Noto'g'ri API key yoki bot faol emas"}, status=status.HTTP_401_UNAUTHORIZED)

    question = request.data.get('message')
    session_id = request.data.get('session_id')

    if not question:
        return Response({"error": "message kerak"}, status=status.HTTP_400_BAD_REQUEST)

    if not session_id:
        session_id = str(uuid.uuid4())

    conversation, _ = Conversation.objects.get_or_create(
        bot=bot,
        channel=Conversation.Channel.WEBSITE,
        external_chat_id=session_id,
        defaults={'chat_type': Conversation.ChatType.PRIVATE}
    )

    Message.objects.create(conversation=conversation, sender=Message.Sender.USER, content=question)

    try:
        answer, usage = get_bot_response(bot, question)
    except Exception as e:
        logger.exception(f"Bot javob berishda xato (bot_id={bot.id}): {e}")
        answer, usage = (bot.fallback_message or "Kechirasiz, xatolik yuz berdi."), None

    if answer is None:
        answer = bot.fallback_message or "Kechirasiz, javob topa olmadim."

    Message.objects.create(
        conversation=conversation,
        sender=Message.Sender.BOT,
        content=answer,
        prompt_tokens=usage["prompt_tokens"] if usage else None,
        completion_tokens=usage["completion_tokens"] if usage else None,
        total_tokens=usage["total_tokens"] if usage else None,
        model_used=usage["model"] if usage else None,
        cost_usd=usage["cost_usd"] if usage else None,
    )

    return Response({
        "answer": answer,
        "session_id": session_id
    })