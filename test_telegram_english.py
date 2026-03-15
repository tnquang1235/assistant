
import os
import pytz
from datetime import datetime
from config import settings
from modules.google_sheets import GoogleSheetManager
from modules.notifier import TelegramNotifier
from modules.english import EnglishModule

from unittest.mock import MagicMock

def test_telegram_evening_simulation():
    print("--- Mo phong ban tin buoi toi (Evening) - KHONG thay doi du lieu ---")
    
    # 1. Khoi tao cac module
    bot = TelegramNotifier(settings.BOT_TOKEN, settings.CHAT_ID)
    gs_eng = GoogleSheetManager(settings.GOOGLE_CREDENTIAL_FILE, settings.ENGLISH_SHEET_ID, notifier=bot)
    eng = EnglishModule(gs_eng, sheet_name=settings.ENGLISH_SHEET_NAME)
    
    # QUAN TRONG: Mock ham _update_srs de khong lam thay doi du lieu next_review tren Sheet khi test
    eng._update_srs = MagicMock()
    # Mock luon ca update_cell_by_match de bao ve du lieu date_learned neu vo tinh co tu moi
    gs_eng.update_cell_by_match = MagicMock()
    
    # 2. Lay du lieu thuc te (Mo phong buoi toi: 0 tu moi, tat ca recap va tat ca old review)
    # Vi da mock _update_srs nen lenh nay an toan, khong ghi de Sheet
    new_w, recap_w, old_w = eng.get_session_words(num_new=0, num_recap=None, num_old=None)
    
    print(f"Ket qua loc: {len(recap_w)} Recap, {len(old_w)} Old Review (Nhom nay se khong bi update ngay on tap).")

    # 3. Tao noi dung ban tin buoi toi
    title = "BAN TIN TIENG ANH BUOI TOI (Simulation)"
    
    report = eng.format_bulletin(title, new_words=None, recap_words=recap_w, old_words=old_w)
    
    # Gui thu qua Telegram
    bot.send(report)
    print("[OK] Da gui ban tin mo phong buoi toi qua Telegram!")

if __name__ == "__main__":
    test_telegram_evening_simulation()
