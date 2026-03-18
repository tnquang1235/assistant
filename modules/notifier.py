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

    def send_photo(self, photo_path, caption=None):
        """Gửi ảnh qua Telegram."""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
        try:
            with open(photo_path, 'rb') as photo:
                files = {'photo': photo}
                payload = {'chat_id': self.chat_id}
                if caption:
                    payload['caption'] = caption
                    payload['parse_mode'] = 'HTML'
                response = requests.post(url, data=payload, files=files)
                if response.status_code != 200:
                    print(f"❌ Telegram Photo Error: {response.text}")
                else:
                    print(f"✅ Đã gửi ảnh lỗi qua Telegram: {photo_path}")
        except Exception as e:
            print(f"❌ Telegram Photo Connection Error: {e}")
