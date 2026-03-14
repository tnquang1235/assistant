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

# ================= INITIALIZATION =================

bot = TelegramNotifier(settings.BOT_TOKEN, settings.CHAT_ID)

# Separate managers for each module
gs_fin = GoogleSheetManager(settings.GOOGLE_CREDENTIAL_FILE, settings.FINANCE_SHEET_ID)
gs_weather = GoogleSheetManager(settings.GOOGLE_CREDENTIAL_FILE, settings.WEATHER_SHEET_ID)
gs_eng = GoogleSheetManager(settings.GOOGLE_CREDENTIAL_FILE, settings.ENGLISH_SHEET_ID)

fin = FinanceModule(gs_fin, sheet_name=settings.FINANCE_SHEET_NAME)
weather = WeatherModule(settings.WEATHER_API_KEY, gs_weather, sheet_name=settings.WEATHER_SHEET_NAME)
eng = EnglishModule(gs_eng, sheet_name=settings.ENGLISH_SHEET_NAME)

# Configuration for vocabulary distribution (Flexible counts per session)
# Cấu hình phân bổ từ vựng (Số lượng linh hoạt cho mỗi buổi)
# new: từ mới toanh, recap: ôn từ mới trong ngày (None = lấy tất cả danh sách hiện có)
# old_ratio: Tỉ lệ từ cũ cần ôn, nhập theo số thập phân (ví dụ: 0.1 = 1/10, 0.2 = 2/10).
# Buổi cuối cùng (Evening) để None để máy tính tự dồn toàn bộ số từ còn sót lại trong ngày.
ENGLISH_CONFIG = {
    "Morning":   {"new": 2, "recap": 0,    "old_ratio": 0.0},
    "Noon":      {"new": 2, "recap": 2,    "old_ratio": 0.1},
    "Afternoon": {"new": 1, "recap": 4,    "old_ratio": 0.4},
    "Evening":   {"new": 0, "recap": None, "old_ratio": None}
}

# ================= HELPERS =================

def get_current_greeting():
    """Returns a greeting based on the current system hour."""
    hour = datetime.now().hour
    
    if 5 <= hour < 11:
        return "🌅 Good morning!"
    elif 11 <= hour < 13:
        return "🕛 Good noon!"
    elif 13 <= hour < 18:
        return "🕓 Good afternoon!"
    elif 18 <= hour < 22:
        return "🌙 Good evening!"
    else:
        return "🌌 Good night!"

# ================= TASKS =================

def send_bulletin(session_name, is_first_run=False):
    """Orchestrates the bulletin in the requested order."""
    print(f"🔔 Running {session_name} Bulletin...")
    
    # 1. Lời chào & Thông tin thời tiết
    bot.send(f"{get_current_greeting()}\n\n" + weather.get_report())

    # 2. Từ vựng tiếng Anh
    if not (session_name == "Morning" and is_first_run):
        conf = ENGLISH_CONFIG.get(session_name, {})
        
        # Tự động tính target / remaining theo chuỗi tỉ lệ
        old_ratio_val = conf.get("old_ratio")
        calculated_ratio = None
        if old_ratio_val is not None:
            # Tính tổng các tỉ lệ đã đi qua ở các buổi trước
            ratio_done = 0.0
            for s in ["Morning", "Noon", "Afternoon", "Evening"]:
                if s == session_name:
                    break
                s_ratio = ENGLISH_CONFIG.get(s, {}).get("old_ratio")
                if isinstance(s_ratio, (int, float)):
                    ratio_done += float(s_ratio)
            
            calculated_ratio = {
                "target": float(old_ratio_val),
                "remaining": max(0.01, 1.0 - ratio_done) # max chống lỗi chia cho 0
            }

        new_w, recap_w, old_w = eng.get_session_words(
            num_new=conf.get("new", 0), 
            num_recap=conf.get("recap", 0), 
            old_ratio=calculated_ratio
        )
        title = f"HỌC TIẾNG ANH ({session_name})"
        bot.send(eng.format_bulletin(title, new_w, recap_w, old_w))

    # 3. Thị trường thế giới
    mode = "full" if session_name == "Morning" else "highlights"
    bot.send(fin.get_report(mode=mode))

    # 4. Chứng khoán Việt Nam (Note TODO)
    # vn_stock_todo = (
    #     "🇻🇳 <b>CHỨNG KHOÁN VIỆT NAM (TODO)</b>\n"
    #     "<i>Dự kiến phát triển:</i>\n"
    #     "• Theo dõi chỉ số VN-Index, HNX-Index.\n"
    #     "• Top 5 cổ phiếu thanh khoản cao nhất.\n"
    #     "• Cảnh báo vùng mua/bán theo kỹ thuật (RSI/MACD).\n"
    #     "• Gợi ý: Tích hợp API từ SSI hoặc VNDirect if available."
    # )
    # bot.send(vn_stock_todo)

def morning_job(is_first_run=False):
    send_bulletin("Morning", is_first_run)

def noon_job():
    send_bulletin("Noon")

def afternoon_job():
    send_bulletin("Afternoon")

def evening_job():
    send_bulletin("Evening")
    bot.send("🌙 Bye!")

# ================= SCHEDULING =================

schedule.every().day.at("06:00").do(morning_job)
schedule.every().day.at("12:00").do(noon_job)
schedule.every().day.at("16:00").do(afternoon_job)
schedule.every().day.at("22:00").do(evening_job)

# Chạy thử kiểm tra khi khởi động
# morning_job()

if __name__ == "__main__":
    print("🚀 Assistant v1.2 đang chạy với cấu trúc Modular...")
    
    # Lần chạy đầu tiên: Chỉ cập nhật weather/finance, không học tiếng Anh
    morning_job(is_first_run=True)

    while True:
        schedule.run_pending()
        time.sleep(60)
