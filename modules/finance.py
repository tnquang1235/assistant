import yfinance as yf
import pytz
import pandas as pd
from datetime import datetime

class FinanceModule:
    """
    Xử lý dữ liệu tài chính và tạo bản tin thị trường thế giới.
    """
    # Danh sách các chỉ số tài chính quan trọng
    FIN_SYMBOLS = {
        # ===================== US =====================
        "S&P500": "^GSPC",        # United States – S&P 500
        "DowJones": "^DJI",       # United States – Dow Jones Industrial Average
        "Nasdaq": "^IXIC",        # United States – Nasdaq Composite

        # ===================== Europe =====================
        "EuroStoxx50": "^STOXX50E",  # Eurozone – Euro Stoxx 50
        "DAX": "^GDAXI",             # Germany – DAX
        "CAC40": "^FCHI",            # France – CAC 40
        "FTSE100": "^FTSE",          # United Kingdom – FTSE 100
        "IBEX35": "^IBEX",           # Spain – IBEX 35
        "FTSEMIB": "FTSEMIB.MI",     # Italy – FTSE MIB

        # ===================== Asia =====================
        "Nikkei225": "^N225",        # Japan – Nikkei 225
        "KOSPI": "^KS11",            # South Korea – KOSPI
        "HangSeng": "^HSI",          # Hong Kong – Hang Seng Index
        "ShanghaiComp": "^SSEC",     # China – Shanghai Composite
        "CSI300": "000300.SS",       # China – CSI 300
        "NIFTY50": "^NSEI",          # India – NIFTY 50
        "Sensex": "^BSESN",          # India – BSE Sensex
        "STI": "^STI",               # Singapore – Straits Times Index
        "SET": "^SET.BK",            # Thailand – SET Index
        "JKSE": "^JKSE",             # Indonesia – Jakarta Composite Index
        "KLSE": "^KLSE",             # Malaysia – FTSE Bursa Malaysia KLCI
        "PSEi": "^PSI",              # Philippines – PSE Index
        
        # ===================== Commodities =====================
        "Gold": "GC=F",              # Gold Futures (COMEX)
        "Silver": "SI=F",            # Silver Futures (COMEX)

        # ===================== Crypto =====================
        "Bitcoin": "BTC-USD"         # Bitcoin / USD
    }

    # Mapping emojis (flags/logos) cho từng chỉ số
    FIN_EMOJIS = {
        "S&P500": "🇺🇸", "DowJones": "🇺🇸", "Nasdaq": "🇺🇸",
        "EuroStoxx50": "🇪🇺", "DAX": "🇩🇪", "CAC40": "🇫🇷", "FTSE100": "🇬🇧", "IBEX35": "🇪🇸", "FTSEMIB": "🇮🇹",
        "Nikkei225": "🇯🇵", "KOSPI": "🇰🇷", "HangSeng": "🇭🇰", "ShanghaiComp": "🇨🇳", "CSI300": "🇨🇳",
        "NIFTY50": "🇮🇳", "Sensex": "🇮🇳", "STI": "🇸🇬", "SET": "🇹🇭", "JKSE": "🇮🇩", "KLSE": "🇲🇾", "PSEi": "🇵🇭",
        "Gold": "🥇", "Silver": "🥈", "Bitcoin": "⚡"
    }


    def __init__(self, google_manager, sheet_name="daily_fin", timezone="Asia/Ho_Chi_Minh"):
        self.gs = google_manager
        self.sheet_name = sheet_name
        self.tz = pytz.timezone(timezone)

    def _get_pct_change(self, current, historical):
        if historical == 0 or historical is None: return 0
        return ((current - historical) / historical) * 100

    def get_report(self, mode="full"):
        """Tạo bản tin tài chính chuyên nghiệp với dữ liệu 1D, 1W, 1M, 1Q, 1Y."""
        print(f"📊 Đang truy xuất dữ liệu thị trường (chế độ: {mode})...")
        now = datetime.now(self.tz)
        
        # Lọc bỏ VNINDEX nếu có (theo yêu cầu hệ thống)
        symbols_to_fetch = {k: v for k, v in self.FIN_SYMBOLS.items() if k != "VNINDEX" and v != "^VNI"}
        tickers = list(symbols_to_fetch.values())
        
        # Tải dữ liệu lịch sử 2 năm để tính các mốc 1W, 1M, 1Y
        df_hist = yf.download(tickers, period="2y", group_by="ticker", auto_adjust=True, progress=False)
        
        all_data = []
        rows_to_update = []

        for name, ticker in symbols_to_fetch.items():
            try:
                data = df_hist[ticker].dropna()
                if data.empty: continue
                
                # Lấy giá đóng cửa mới nhất và ngày dữ liệu tương ứng làm gốc
                curr_p = float(data.iloc[-1]["Close"])
                base_date = data.index[-1]
                
                # Hàm tính biến động % linh hoạt
                def calc_chg_flexible(period_type):
                    try:
                        if period_type == "1D":
                            if len(data) >= 2:
                                prev_p = float(data.iloc[-2]["Close"])
                                return self._get_pct_change(curr_p, prev_p)
                        else:
                            # Xác định ngày mục tiêu dựa trên ngày dương lịch
                            if period_type == "1W":
                                target_date = base_date - pd.DateOffset(weeks=1)
                            elif period_type == "1M":
                                target_date = base_date - pd.DateOffset(months=1)
                            elif period_type == "1Q":
                                target_date = base_date - pd.DateOffset(months=3)
                            elif period_type == "1Y":
                                target_date = base_date - pd.DateOffset(years=1)
                            else:
                                return 0
                            
                            # Tìm ngày giao dịch gần nhất (lùi về quá khứ) so với ngày mục tiêu
                            available_dates = data.index[data.index <= target_date]
                            if not available_dates.empty:
                                prev_p = float(data.loc[available_dates[-1]]["Close"])
                                return self._get_pct_change(curr_p, prev_p)
                        return 0
                    except Exception:
                        return 0

                c1d = calc_chg_flexible("1D") # 1 Day (Phiên liền trước)
                c1w = calc_chg_flexible("1W") # 1 Week (Đúng 7 ngày trước hoặc gần nhất)
                c1m = calc_chg_flexible("1M") # 1 Month (Cùng ngày tháng trước)
                c1q = calc_chg_flexible("1Q") # 1 Quarter (3 tháng trước)
                c1y = calc_chg_flexible("1Y") # 1 Year (Cùng ngày năm trước)
                
                all_data.append({
                    "name": name, "price": curr_p, 
                    "c1d": c1d, "c1w": c1w, "c1m": c1m, "c1q": c1q, "c1y": c1y
                })
                
                # Chuẩn bị dữ liệu cập nhật Google Sheets (Dùng ngày gốc từ dữ liệu)
                rows_to_update.append({
                    "date": base_date.strftime("%Y-%m-%d"),
                    "timestamp": now.strftime("%Y-%m-%d %H:%M"),
                    "symbol": name,
                    "close": round(curr_p, 2),
                    "volume": int(data.iloc[-1]["Volume"]) if "Volume" in data.columns else 0,
                })
            except Exception as e:
                print(f"⚠️ Lỗi xử lý {name}: {e}")

        # Logic sắp xếp: Mạnh -> Yếu (Giảm dần theo biến động 1D)
        display_data = sorted(all_data, key=lambda x: x["c1d"], reverse=True)
        
        # Nếu không phải bản tin Sáng (full), chỉ lấy Top 3 tăng và Top 3 giảm
        if mode != "full":
            if len(display_data) > 6:
                display_data = display_data[:3] + display_data[-3:]

        title = "📊 <b>THỊ TRƯỜNG THẾ GIỚI</b>"
        if mode == "full":
            title += " (Full)"
        else:
            title += " (Top)"
        
        # Tạo bảng định dạng tối ưu cho Telegram (hiển thị tốt trên nhiều nền tảng, kể cả Mobile)
        report = f"{title}\n<pre>"
        # Index: 14, Now: 8, 1D: 8, Các kỳ khác: 5-6 (Tối ưu để không bị vỡ dòng trên màn hình nhỏ)
        report += f"{'Index':<14} {'Now':>8} {'1D':>8} {'1W':>5} {'1M':>5} {'1Q':>5} {'1Y':>6}\n"
        report += "-" * 58 + "\n"

        for d in display_data:
            emoji = self.FIN_EMOJIS.get(d['name'], "🔹")
            # Tạo nhãn: Emoji + Khoảng trắng + Tên
            name_label = f"{emoji} {d['name']}"
            
            # Tính toán khoảng đệm (padding) thủ công để xử lý Emoji 2-cell
            # - Emoji cờ (🇺🇸): len()=2, visual_width=2. Khớp.
            # - Emoji tròn (🟡, ⚪, 🪙): len()=1, nhưng visual_width=2. Cần bù +1.
            # - Bitcoin sign (₿): len()=1, visual_width=1. Khớp.
            visual_len = len(name_label)
            
            # Các emoji 1-char nhưng rộng (wide)
            if emoji in ["🟡", "⚪", "🪙", "🟠", "🟢", "🔴", "🥇", "🥈", "💎", "💰", "💹", "⚡"]:
                visual_len += 1
            
            padding = " " * max(0, 14 - visual_len)
            row_label = f"{name_label}{padding}"[:14]

            # Định dạng Snapshot: 1D cần chi tiết (2 số thập phân), các kỳ xa hơn lấy số nguyên để gọn
            report += (f"{row_label} {d['price']:>8.1f} "
                       f"{d['c1d']:>+7.2f}% {d['c1w']:>+4.0f}% {d['c1m']:>+4.0f}% "
                       f"{d['c1q']:>+4.0f}% {d['c1y']:>+5.0f}%\n")

        """
        💡 HƯỚNG DẪN ĐỊNH DẠNG BẢNG (F-STRING FORMATTING):
        ------------------------------------------------
        Cấu trúc mẫu: {giá_trị : [căn_lề][dấu][độ_rộng].[thập_phân][kiểu]}
        
        1. Tiêu đề (Header): {'1W':>6}
           - [>]: Căn lề phải.
           - [6]: Độ rộng ô là 6 ký tự.
           
        2. Dữ liệu (Data): {biến : >+5.1f}%
           - [>]: Căn lề phải.
           - [+]: Luôn hiển thị dấu (+) hoặc (-) phía trước số.
           - [5]: Độ rộng phần số là 5 ký tự.
           - [.1]: Lấy 1 chữ số sau dấu thập phân.
           - [f]: Kiểu số thực (float).
           - [%]: Ký tự đơn vị đứng sau (chiếm thêm 1 khoảng trống).
           => Tổng độ rộng (5 + 1) = 6 ký tự, khớp hoàn hảo với Tiêu đề.

        Báo cáo Telegram ưu tiên tính "Snapshot" (nhanh, gọn, không vỡ dòng trên mobile).
        
        1. Cột 1D (Phiên gần nhất): {biến : >+7.2f}% 
           - Lấy 2 số thập phân để theo dõi sát biến động (độ nhạy cao) hàng ngày.
           - Tổng độ rộng: 7 (số) + 1 (%) = 8 ký tự.
           
        2. Các cột 1W, 1M, 1Q, 1Y: {biến : >+4.0f}% hoặc >+5.0f}%
           - Lấy số nguyên (.0f) để tiết kiệm không gian, phù hợp xem nhanh xu hướng.
           - Độ rộng linh hoạt (5-6 ký tự) giúp bảng tổng thể không quá dài.
        """
        report += "</pre>"

        # Cập nhật dữ liệu lên Google Sheets
        if rows_to_update:
            self.gs.update_financial_optimized(self.sheet_name, rows_to_update)
            
        return report
