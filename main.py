import schedule
import time
import pytz
from datetime import datetime
from config import settings # Giả định file config/settings vẫn tồn tại như v1.1

from modules.google_sheets import GoogleSheetManager
from modules.notifier import TelegramNotifier
from modules.finance import FinanceModule
from modules.weather import WeatherModule
from modules.english import EnglishModule
from modules.vn_finance import VNFinanceModule

# ================= INITIALIZATION =================

bot = TelegramNotifier(settings.BOT_TOKEN, settings.CHAT_ID)

# Separate managers for each module
gs_fin = GoogleSheetManager(settings.GOOGLE_CREDENTIAL_FILE, settings.FINANCE_SHEET_ID, notifier=bot)
gs_weather = GoogleSheetManager(settings.GOOGLE_CREDENTIAL_FILE, settings.WEATHER_SHEET_ID, notifier=bot)
gs_eng = GoogleSheetManager(settings.GOOGLE_CREDENTIAL_FILE, settings.ENGLISH_SHEET_ID, notifier=bot)

vn_sheet_id = getattr(settings, 'VN_FINANCE_SHEET_ID', None)
if not vn_sheet_id:
    print("[WARN] VN_FINANCE_SHEET_ID missing. VN-Index data will not be saved to Sheets.")
    class MockGS:
        def update_financial_optimized(self, sheet_name, data):
            pass
    gs_vn = MockGS()
else:
    try:
        gs_vn = GoogleSheetManager(settings.GOOGLE_CREDENTIAL_FILE, vn_sheet_id, notifier=bot)
    except Exception as e:
        print(f"[WARN] Failed to connect VN_FINANCE_SHEET_ID: {e}")
        class MockGS:
            def update_financial_optimized(self, sheet_name, data):
                pass
        gs_vn = MockGS()

fin = FinanceModule(gs_fin, sheet_name=settings.FINANCE_SHEET_NAME)
weather = WeatherModule(settings.WEATHER_API_KEY, gs_weather, sheet_name=settings.WEATHER_SHEET_NAME)
eng = EnglishModule(gs_eng, sheet_name=settings.ENGLISH_SHEET_NAME)
vn_fin = VNFinanceModule(gs_vn)

# Configuration for vocabulary distribution (Flexible counts per session)
# Cấu hình phân bổ từ vựng (Số lượng linh hoạt cho mỗi buổi)
# new: từ mới toanh, recap: ôn từ mới trong ngày, old: ôn từ cũ các ngày trước
# None = lấy tất cả danh sách hiện có của nhóm đó
ENGLISH_CONFIG = {
    "Morning":   {"new": 2, "recap": 0, "old": 5},
    "Noon":      {"new": 2, "recap": 2, "old": 5},
    "Afternoon": {"new": 1, "recap": 4, "old": 5},
    "Evening":   {"new": 0, "recap": None, "old": None}
}

# ================= TASKS (ATOMIC FUNCTIONS) =================

def task_greeting_weather():
    """Tự động chọn lời chào theo thời gian và gửi báo cáo thời tiết."""
    hour = datetime.now().hour
    if 5 <= hour < 11:
        greeting = "🌅 Chào buổi sáng!"
    elif 11 <= hour < 14:
        greeting = "🕛 Chào buổi trưa!"
    elif 14 <= hour < 18:
        greeting = "🕓 Chào buổi chiều!"
    else:
        greeting = "🌙 Chúc buổi tối tốt lành!"
        
    bot.send(f"{greeting}\n\n" + weather.get_report())

def task_english_vocab(session_name, config):
    """Xử lý và gửi bài học tiếng Anh theo cấu hình."""
    """Cấu hình phân bổ từ vựng mỗi phiên tại ENGLISH_CONFIG"""
    new_w, recap_w, old_w = eng.get_session_words(
        num_new=config.get("new", 0), 
        num_recap=config.get("recap", 0), 
        num_old=config.get("old", 0)
    )
    title = f"HỌC TIẾNG ANH ({session_name})"
    bot.send(eng.format_bulletin(title, new_w, recap_w, old_w))

def task_market_world(mode="highlights"):
    """Gửi báo cáo thị trường tài chính thế giới."""
    bot.send(fin.get_report(mode=mode))

def task_market_vn(session_name, goodbye=None):
    """Gửi báo cáo chứng khoán Việt Nam và lời chào kết thúc nếu có."""
    report = vn_fin.get_report(session=session_name)
    if goodbye:
        report += f"\n\n{goodbye}"
    bot.send(report)

# ================= SESSION JOBS =================

def morning_job(is_first_run=False):
    """Bản tin tổng hợp đầu ngày (Global Snapshot)."""
    print(f"🔔 Running Global Snapshot Bulletin...")
    # 1. Chào hỏi & Thời tiết (Tự động)
    task_greeting_weather()
    # 2. Tiếng Anh (Giữ nguyên tên 'Morning' để không đổi bản tin)
    if not is_first_run:
        eng_conf = ENGLISH_CONFIG.get("Morning")
        task_english_vocab("Morning", eng_conf)
    # 3. Tài chính thế giới (Full report vào buổi sáng)
    task_market_world(mode="full")
    # 4. Chứng khoán VN -> Bỏ ra khỏi bản tin 6h sáng theo yêu cầu

def vn_market_watch_job(session_name):
    """Bản tin cập nhật chứng khoán VN."""
    print(f"🔔 Running {session_name}...")
    task_market_vn(session_name)

def noon_job():
    """Điểm tin giữa ngày."""
    print(f"🔔 Running Mid-day Recap...")
    
    task_greeting_weather()
    # Tiếng Anh giữ nguyên tên 'Noon'
    task_english_vocab("Noon", ENGLISH_CONFIG.get("Noon"))
    task_market_world(mode="highlights")
    task_market_vn("MID_DAY_RECAP")

def afternoon_job():
    """Tổng kết phiên giao dịch."""
    print(f"🔔 Running Market Closing Summary...")
    
    task_greeting_weather()
    # Tiếng Anh giữ nguyên tên 'Afternoon'
    task_english_vocab("Afternoon", ENGLISH_CONFIG.get("Afternoon"))
    task_market_world(mode="highlights")
    task_market_vn("MARKET_CLOSE_SUMMARY")

def evening_job():
    """Đánh giá cuối ngày."""
    print(f"🔔 Running Day-end Review...")
    
    task_greeting_weather()
    # Tiếng Anh giữ nguyên tên 'Evening'
    task_english_vocab("Evening", ENGLISH_CONFIG.get("Evening"))
    task_market_world(mode="highlights")
    task_market_vn("DAY_END_REVIEW", goodbye="🌙 Good night!")

# ================= SCHEDULING =================

schedule.every().day.at("06:00").do(morning_job)
schedule.every().day.at("08:00").do(vn_market_watch_job, session_name="MARKET_OPENING")
schedule.every().day.at("10:00").do(vn_market_watch_job, session_name="MARKET_WATCH")
schedule.every().day.at("12:00").do(noon_job)
schedule.every().day.at("16:00").do(afternoon_job)
schedule.every().day.at("22:00").do(evening_job)

# Chạy thử kiểm tra khi khởi động
# morning_job()

if __name__ == "__main__":
    print("🚀 Assistant v1.3 đang chạy với cấu trúc Modular và VN-Index Support...")
    
    # Lần chạy đầu tiên: Chỉ cập nhật weather/finance, không học tiếng Anh
    morning_job(is_first_run=True)

    while True:
        schedule.run_pending()
        time.sleep(60)
