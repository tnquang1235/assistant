import time
import sys
import io

# Cấu hình encoding cho terminal Windows (Tránh lỗi Emoji/Unicode)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from config import settings
from modules.google_sheets import GoogleSheetManager
from modules.notifier import TelegramNotifier
from modules.vn_finance import VNFinanceModule

# ================= INITIALIZATION =================
# Hoạt động giống main.py nhưng chỉ khởi tạo các thành phần cần thiết cho VN Finance

bot = TelegramNotifier(settings.BOT_TOKEN, settings.CHAT_ID)

# VN_FINANCE_SHEET_ID có thể bị thiếu trong .env, ta sẽ tạo dummy manager nếu cần
# hoặc fallback về một ID hợp lệ để test logic lấy dữ liệu (scrape)
vn_sheet_id = getattr(settings, 'VN_FINANCE_SHEET_ID', None)

if not vn_sheet_id:
    print("[INFO] VN_FINANCE_SHEET_ID missing in .env. Logging data without updating Google Sheets.")
    class MockGS:
        def update_financial_optimized(self, sheet_name, data):
            print(f"[DEBUG] MockGS would update sheet '{sheet_name}' with {len(data)} records.")
    gs_vn = MockGS()
else:
    try:
        gs_vn = GoogleSheetManager(settings.GOOGLE_CREDENTIAL_FILE, vn_sheet_id)
    except Exception as e:
        print(f"[WARN] Could not connect to Google Sheets: {e}")
        class MockGS:
            def update_financial_optimized(self, sheet_name, data):
                print(f"[DEBUG] MockGS (Fallback): {len(data)} records processed.")
        gs_vn = MockGS()

vn_fin = VNFinanceModule(gs_vn)

def test_vn_finance_job():
    """
    Chỉ tập trung chạy chức năng vn_finance
    """
    print(f"[*] [{time.strftime('%Y-%m-%d %H:%M:%S')}] Running VN Finance Test...")
    
    try:
        # Lấy báo cáo vn_finance với session="Afternoon"
        report = vn_fin.get_report(session="Afternoon")
        
        print("\n--- REPORT CONTENT BEGIN ---")
        print(report)
        print("--- REPORT CONTENT END ---\n")
        
        # Gửi qua Telegram
        bot.send(report)
        print("[+] Message command sent to Telegram notifier successfully.")
        
    except Exception as e:
        import traceback
        print(f"[-] Error during VN Finance Test: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print("[*] Khởi động script kiểm tra VN Finance...")
    test_vn_finance_job()
    print("[*] Kết thúc kiểm tra.")
