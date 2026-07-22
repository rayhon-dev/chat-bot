import logging
import requests

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/{method}"
MAX_MESSAGE_LENGTH = 4000


def _call_telegram_api(bot_token, method, payload):
    url = TELEGRAM_API_BASE.format(token=bot_token, method=method)
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Telegram API xatosi ({method}): {e}")
        return None


def send_message(bot_token, chat_id, text, reply_to_message_id=None):
    if not text:
        return

    for i in range(0, len(text), MAX_MESSAGE_LENGTH):
        chunk = text[i:i + MAX_MESSAGE_LENGTH]
        payload = {"chat_id": chat_id, "text": chunk}

        if reply_to_message_id and i == 0:
            payload["reply_to_message_id"] = reply_to_message_id

        _call_telegram_api(bot_token, "sendMessage", payload)


def send_chat_action(bot_token, chat_id, action="typing"):
    _call_telegram_api(bot_token, "sendChatAction", {"chat_id": chat_id, "action": action})