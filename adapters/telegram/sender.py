import requests


def send_message(bot_token, chat_id, text, reply_to_message_id=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id
    response = requests.post(url, json=payload, timeout=10)
    return response.json()


def send_chat_action(bot_token, chat_id, action="typing"):
    url = f"https://api.telegram.org/bot{bot_token}/sendChatAction"
    requests.post(url, json={"chat_id": chat_id, "action": action}, timeout=5)