
import os
from config import settings
from modules.google_sheets import GoogleSheetManager
from datetime import datetime
import pytz

def diagnostic():
    print("--- Diagnostic English Sheet Dates ---")
    gs = GoogleSheetManager(settings.GOOGLE_CREDENTIAL_FILE, settings.ENGLISH_SHEET_ID)
    all_vocab = gs.get_all_records(settings.ENGLISH_SHEET_NAME)
    
    tz = pytz.timezone("Asia/Ho_Chi_Minh")
    now_date = datetime.now(tz).strftime("%Y-%m-%d")
    print(f"Server now_date: {now_date}")
    
    if not all_vocab:
        print("Sheet is empty!")
        return

    print("\nRows with next_review data analysis:")
    found = 0
    for i, w in enumerate(all_vocab):
        word = w.get("word")
        dl = w.get("date_learned")
        nr = w.get("next_review")
        if nr:
            print(f"[{i}] Word: {word} | date_learned: '{dl}' | next_review: '{nr}'")
            found += 1
            if found >= 10: break

    # Kiem tra xem co tu nao khop ngay hom nay khong
    recap_count = sum(1 for w in all_vocab if str(w.get("date_learned") or "").strip() == now_date)
    print(f"\nRecap count found for {now_date}: {recap_count}")

    # Kiem tra logic is_due
    due_count = 0
    for w in all_vocab:
        next_review = str(w.get("next_review") or "").strip()
        learned_date = str(w.get("date_learned") or "").strip()
        if not next_review or next_review == "DONE": continue
        if next_review <= now_date and learned_date != now_date:
            due_count += 1
    print(f"Old review count found: {due_count}")

if __name__ == "__main__":
    diagnostic()
