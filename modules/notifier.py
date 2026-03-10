import requests

class TelegramNotifier:
    """
    Xử lý gửi thông báo qua Telegram.
    """
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    def send(self, message):
        """Gửi tin nhắn văn bản (hỗ trợ HTML)."""
        payload = {
            "chat_id": self.chat_id, 
            "text": message, 
            "parse_mode": "HTML"
        }
        try:
            response = requests.post(self.base_url, data=payload)
            if response.status_code != 200:
                print(f"❌ Telegram Error: {response.text}")
        except Exception as e:
            print(f"❌ Telegram Connection Error: {e}")
