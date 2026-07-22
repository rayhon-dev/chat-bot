from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from clients.models import Bot
from conversations.models import Conversation, Message
from rag.services.chat import get_bot_response
import uuid


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
        channel='website',
        external_chat_id=session_id,
        defaults={'chat_type': 'private'}
    )

    Message.objects.create(conversation=conversation, sender='user', content=question)

    answer = get_bot_response(bot, question)

    Message.objects.create(conversation=conversation, sender='bot', content=answer)

    return Response({
        "answer": answer,
        "session_id": session_id
    })