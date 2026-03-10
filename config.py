import os
from dotenv import load_dotenv

load_dotenv()  # đọc .env

class Settings:
    def __init__(self):
        self.BOT_TOKEN = os.getenv("BOT_TOKEN")
        self.WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
        self.CHAT_ID = os.getenv("CHAT_ID")
        self.GOOGLE_CREDENTIAL_FILE = os.getenv("GOOGLE_CREDENTIAL_FILE")
        
        # Module-specific IDs
        self.ENGLISH_SHEET_ID = os.getenv("ENGLISH_SHEET_ID")
        self.ENGLISH_SHEET_NAME = os.getenv("ENGLISH_SHEET_NAME", "english_vocab")
        
        self.FINANCE_SHEET_ID = os.getenv("FINANCE_SHEET_ID")
        self.FINANCE_SHEET_NAME = os.getenv("FINANCE_SHEET_NAME", "daily_fin")
        
        self.WEATHER_SHEET_ID = os.getenv("WEATHER_SHEET_ID")
        self.WEATHER_SHEET_NAME = os.getenv("WEATHER_SHEET_NAME", "weather")

        self._validate()

    def _validate(self):
        required_vars = {
            "BOT_TOKEN": self.BOT_TOKEN,
            "WEATHER_API_KEY": self.WEATHER_API_KEY,
            "CHAT_ID": self.CHAT_ID,
            "GOOGLE_CREDENTIAL_FILE": self.GOOGLE_CREDENTIAL_FILE,
            "ENGLISH_SHEET_ID": self.ENGLISH_SHEET_ID,
            "FINANCE_SHEET_ID": self.FINANCE_SHEET_ID,
            "WEATHER_SHEET_ID": self.WEATHER_SHEET_ID,
        }

        missing = [key for key, value in required_vars.items() if not value]

        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")

settings = Settings()