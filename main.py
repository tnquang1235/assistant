# pip install yfinance requests schedule pytz gspread oauth2client psycopg2-binary
# pip install python-dotenv

import os
import requests
import yfinance as yf
import schedule
import time
import pytz
import gspread
import psycopg2
import tkinter as tk
import pandas as pd
from tkinter.filedialog import askopenfilename
from google.oauth2.service_account import Credentials
from datetime import datetime
from config import settings

# ================= CONFIG =================

BOT_TOKEN = settings.BOT_TOKEN
WEATHER_API_KEY = settings.WEATHER_API_KEY   #tnquang11011
GOOGLE_CREDENTIAL_FILE = settings.GOOGLE_CREDENTIAL_FILE

CHAT_ID = settings.CHAT_ID
GOOGLE_SHEET_ID = settings.GOOGLE_SHEET_ID
# client_email = "api2026@dataservice11.iam.gserviceaccount.com"
TIMEZONE = "Asia/Ho_Chi_Minh"

FIN_SYMBOLS = {
    "S&P500": "^GSPC",
    "DowJones": "^DJI",
    "Nasdaq": "^IXIC",
    "VNINDEX": "^VNINDEX",
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Bitcoin": "BTC-USD"
}

# =========================================================
# ================= HƯỚNG NÂNG CẤP ========================
# =========================================================
# Supabase (chưa dùng)
SUPABASE_CONFIG = {
    "host": "YOUR_HOST",
    "database": "postgres",
    "user": "postgres",
    "password": "YOUR_PASSWORD",
    "port": 5432
}

# ==========================================


# =========================================================
# ================= GOOGLE MANAGER ========================
# =========================================================

class GoogleSheetManager:
    def __init__(self, credential_file, sheet_key):
        self.credential_file = credential_file
        self.sheet_key = sheet_key
        self.client = None
        self.book = None
        self.sheets_cache = {}
        self._connect()

    def _connect(self):
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file(
            self.credential_file,
            scopes=scope
        )
        self.client = gspread.authorize(creds)
        self.book = self.client.open_by_key(self.sheet_key)
        print("✅ Connected to Google Sheets")

    def get_sheet(self, sheetname):
        try:
            if sheetname not in self.sheets_cache:
                self.sheets_cache[sheetname] = self.book.worksheet(sheetname)
            return self.sheets_cache[sheetname]
        except Exception:
            print("⚠️ Reconnecting Google...")
            self._connect()
            self.sheets_cache = {}
            return self.get_sheet(sheetname)

    def append_dict_rows(self, sheetname, dict_rows, batch_size=500):
        sheet = self.get_sheet(sheetname)
        headers = sheet.row_values(1)

        rows = []
        for data_dict in dict_rows:
            row = [data_dict.get(col, "") for col in headers]
            rows.append(row)

        for i in range(0, len(rows), batch_size):
            sheet.append_rows(rows[i:i+batch_size])

        print(f"✅ Uploaded {len(rows)} rows to {sheetname}")


google_manager = GoogleSheetManager(
    GOOGLE_CREDENTIAL_FILE,
    GOOGLE_SHEET_ID
)

# =========================================================
# ================= TELEGRAM ==============================
# =========================================================

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

# =========================================================
# ================= DAILY FIN UPDATE ======================
# =========================================================

def update_daily_data():
    print("Updating daily_fin sheet...")

    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    timestamp = now.strftime("%Y-%m-%d %H:%M")
    today_str = now.strftime("%Y-%m-%d")

    sheet = google_manager.get_sheet("daily_fin")

    # Lấy toàn bộ cột timestamp để tránh ghi trùng ngày
    existing_dates = set()
    try:
        all_records = sheet.get_all_records()
        for r in all_records:
            ts = r.get("timestamp", "")
            if ts:
                existing_dates.add(ts[:10])
    except:
        pass

    if today_str in existing_dates:
        print("⚠️ Today already updated. Skipping.")
        return

    tickers = list(FIN_SYMBOLS.values())

    df = yf.download(
        tickers,
        period="2d",
        group_by="ticker",
        auto_adjust=False,
        threads=True
    )

    rows = []

    for name, ticker in FIN_SYMBOLS.items():
        try:
            if len(tickers) == 1:
                data = df
            else:
                data = df[ticker]

            latest = data.dropna().iloc[-1]

            data_dict = {
                "timestamp": timestamp,
                "symbol": name,
                "open": round(float(latest["Open"]), 2),
                "high": round(float(latest["High"]), 2),
                "low": round(float(latest["Low"]), 2),
                "close": round(float(latest["Close"]), 2),
                "volume": int(latest["Volume"]),
                "dividends": round(float(latest.get("Dividends", 0)), 4),
                "stock_splits": round(float(latest.get("Stock Splits", 0)), 4),
            }

            rows.append(data_dict)

        except Exception as e:
            print(f"⚠️ Error processing {name}: {e}")

    if rows:
        google_manager.append_dict_rows("daily_fin", rows)

    print("✅ Daily update completed.")

# =========================================================
# ================= WEATHER ===============================
# =========================================================

def get_weather(timestamp):
    cities = ["Ho Chi Minh City", "Can Tho"]
    text = "\n🌤 <b>Thời tiết</b>\n"
    sh_weather = google_manager.get_sheet("weather")
    headers = sh_weather.row_values(1)
    rows = []
    for city in cities:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        data = requests.get(url).json()

        temp = data["main"]["temp"]
        description = data["weather"][0]["description"]

        data_dict = {
            "timestamp": timestamp,
            "city": city,
            "temp": data["main"]["temp"],
            "main":data["weather"][0]["main"],
            "description":data["weather"][0]["description"],
            "feels_like": data["main"]["feels_like"],
            "temp_min": data["main"]["temp_min"],
            "temp_max": data["main"]["temp_max"],
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"],
            "wind_deg": data["wind"]["deg"],
            "clouds": data["clouds"]["all"]
        }

        rows.append(data_dict)

        alert = ""
        if temp > 35:
            alert = " 🔥 Nóng"
        elif temp < 18:
            alert = " ❄️ Lạnh"

        text += f"{city}: {temp}°C | {description}{alert}\n"

    google_manager.append_dict_rows("weather", rows)
    return text
# =========================================================
# ================= DAILY REPORT ==========================
# =========================================================

def daily_report():
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    timestamp = now.strftime("%Y-%m-%d %H:%M")

    message = f"📊 Report {timestamp}\n"
    message += get_weather(timestamp)

    send_telegram(message)

# =========================================================
# ================= MAIN ==================================
# =========================================================

if __name__ == "__main__":
    update_daily_data()
    daily_report()

    schedule.every().day.at("17:30").do(update_daily_data)
    schedule.every().day.at("06:00").do(daily_report)
    schedule.every().day.at("12:00").do(daily_report)
    schedule.every().day.at("16:00").do(daily_report)

    print("Assistant running...")

    while True:
        schedule.run_pending()
        time.sleep(30)
