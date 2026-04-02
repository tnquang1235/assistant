import os
from dotenv import load_dotenv

load_dotenv()  # đọc .env

class Settings:
    def __init__(self):
        self.BOT_TOKEN = os.getenv("BOT_TOKEN")
        self.ENGLISH_BOT_TOKEN = os.getenv("ENGLISH_BOT_TOKEN") or self.BOT_TOKEN  # Default to main bot if not set
        self.WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
        self.CHAT_ID = os.getenv("CHAT_ID")
        self.GOOGLE_CREDENTIAL_FILE = os.getenv("GOOGLE_CREDENTIAL_FILE")
        
        # Module-specific IDs
        self.ENGLISH_SHEET_ID = os.getenv("ENGLISH_SHEET_ID")
        self.ENGLISH_SHEET_NAME = os.getenv("ENGLISH_SHEET_NAME")
        
        self.FINANCE_SHEET_ID = os.getenv("FINANCE_SHEET_ID")
        self.FINANCE_SHEET_NAME = os.getenv("FINANCE_SHEET_NAME")
        
        self.WEATHER_SHEET_ID = os.getenv("WEATHER_SHEET_ID")
        self.WEATHER_SHEET_NAME = os.getenv("WEATHER_SHEET_NAME")

        self.VN_FINANCE_SHEET_ID = os.getenv("VN_FINANCE_SHEET_ID")
        self.VN_FINANCE_SHEET_NAME = os.getenv("VN_FINANCE_SHEET_NAME")

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