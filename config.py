import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        self.BOT_TOKEN = os.getenv("BOT_TOKEN")
        self.WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
        self.CHAT_ID = os.getenv("CHAT_ID")
        self.GOOGLE_CREDENTIAL_FILE = os.getenv("GOOGLE_CREDENTIAL_FILE")

        self._validate()

    def _validate(self):
        required_vars = {
            "BOT_TOKEN": self.BOT_TOKEN,
            "WEATHER_API_KEY": self.WEATHER_API_KEY,
            "CHAT_ID": self.CHAT_ID,
            "GOOGLE_CREDENTIAL_FILE": self.GOOGLE_CREDENTIAL_FILE,
        }

        missing = [key for key, value in required_vars.items() if not value]

        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")

settings = Settings()