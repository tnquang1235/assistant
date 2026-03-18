import re
import pandas as pd
import time
from datetime import datetime
from scc.controller import ChromeController

class VNFinanceModule:
    """
    Module xử lý dữ liệu chứng khoán Việt Nam (VN-Index, VN30, Ngành).
    Sử dụng SCC để cào dữ liệu từ Vietstock.
    """
    
    URL_VN30 = "https://banggia.vietstock.vn/bang-gia/vn30"
    URL_MARKET = "https://banggia.vietstock.vn/"

    def __init__(self, google_manager, notifier=None, chromedriver_path="./chromedriver.exe"):
        self.gs = google_manager
        self.notifier = notifier
        self.chromedriver_path = chromedriver_path

    def _scrape_vn30_data(self):
        """Cào dữ liệu VN30 stocks từ Vietstock."""
        print("🔍 Đang lấy dữ liệu VN30 stocks từ Vietstock...")
        
        # --- Cân chỉnh tài nguyên tự động cho Raspberry Pi / Linux ---
        import platform
        if platform.system() == "Linux":
            # Trên Linux/Raspberry, ChromeDriver nằm ở vị trí khác và cần các flag bypass sandbox/RAM
            d_path = "/usr/bin/chromedriver"
            e_args = ["--no-sandbox", "--disable-dev-shm-usage"]
        else:
            d_path = self.chromedriver_path
            e_args = []
            
        browser = ChromeController(driver_path=d_path, headless=True, extra_args=e_args)
        
        try:
            browser.begin()
            browser.open_new_tab(self.URL_VN30, name='vietstock.vn')
            browser.switch_to_tab('vietstock.vn')
            # browser.wait_xpath('//*[@id="header-container"]/div[@class="logo"]')
            browser.wait_xpath('//*[@id="price-board-body"]', timeout=30)
            
            # Đợi dữ liệu load hoàn toàn (Vietstock load hơi chậm)
            time.sleep(5)
            
            raw_element = browser.get_xpath('//*[@id="price-board-body"]')
            if not raw_element:
                print("❌ Không tìm thấy bảng giá VN30.")
                shot = browser.capture_error("vn30_not_found")
                if self.notifier and shot:
                    self.notifier.send_photo(shot, caption="❌ <b>Lỗi Scraping VN30</b>\nKhông tìm thấy bảng giá Vietstock.")
                return []
                
            raw_text = raw_element.text
            raw_text = raw_text.strip()
            lines = [l.strip() for l in raw_text.split("\n") if l.strip()]

            records = []
            i = 0
            
            columns = [
                "Symbol", "Note",
                "RefPrice", "Ceiling", "Floor",
                "BidPrice3", "BidVol3",
                "BidPrice2", "BidVol2",
                "BidPrice1", "BidVol1",
                "MatchPrice", "MatchVol",
                "Change", "ChangePct",
                "AskPrice1", "AskVol1",
                "AskPrice2", "AskVol2",
                "AskPrice3", "AskVol3",
                "TotalVol",
                "High", "Low", "Avg",
                "ForeignBuy", "ForeignSell"
            ]

            while i < len(lines):
                symbol_raw = lines[i]
                i += 1

                # Skip empty lines
                if i < len(lines) and lines[i] == "":
                    i += 1
                
                if i >= len(lines): break
                
                data_line = lines[i]
                i += 1

                # Detect special marks
                symbol = re.sub(r"\*+", "", symbol_raw)
                mark = ""

                if symbol_raw.endswith("**"):
                    mark = "warning"
                elif symbol_raw.endswith("*"):
                    mark = "event"
                
                # Hàm hỗ trợ parse number thông minh (xử lý '%', lỗi dấu chấm/phẩy)
                def parse_number(p):
                    p = p.replace('%', '').strip()
                    if not p or p == '-': return '0'
                    
                    # Nếu có nhiều hơn 1 dấu phân cách (như 15.525.70 hoặc 1,552,570)
                    if p.count('.') + p.count(',') > 1:
                        last_sep = max(p.rfind('.'), p.rfind(','))
                        suffix = p[last_sep+1:]
                        if len(suffix) == 3:
                            # Chắc chắn là ngắt hàng nghìn, xóa toàn bộ dấu
                            return p.replace('.', '').replace(',', '')
                        else:
                            # Lỗi định dạng vd: 15,525,70 -> Xóa các dấu trước, chỉ giữ dấu cuối làm thập phân
                            int_part = p[:last_sep].replace('.', '').replace(',', '')
                            return int_part + '.' + suffix
                    else:
                        # 0 hoặc 1 dấu phân cách
                        if '.' in p or ',' in p:
                            sep_idx = max(p.rfind('.'), p.rfind(','))
                            if len(p[sep_idx+1:]) == 3:
                                # Dấu ngắt hàng nghìn (vd: 1,552)
                                return p.replace('.', '').replace(',', '')
                            else:
                                # Dấu thập phân (vd: 23.45 hoặc 23,45)
                                return p.replace(',', '.')
                        else:
                            return p
                
                parts = [parse_number(p) for p in data_line.split(" ")]
                
                # Build record
                rec = [symbol, mark] + parts
                
                # Prepare dictionary to keep compatibility with existing code
                record = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "type": "VN30_STOCK",
                    "symbol": symbol,
                    "close": float(parts[9].replace("%", "")) if len(parts) > 9 else 0,        # Same as MatchPrice
                    "change": float(parts[11].replace("%", "")) if len(parts) > 11 else 0,     # Same as Change
                    "change_pct": float(parts[12].replace("%", "")) if len(parts) > 12 else 0, # Same as ChangePct
                    "volume": int(float(parts[19].replace("%", ""))) if len(parts) > 19 else 0 # Same as TotalVol
                }

                # Add all scraped columns into record mapping
                for idx, col_name in enumerate(columns):
                    if idx < len(rec):
                        val = rec[idx]
                        if col_name not in ["Symbol", "Note"] and val:
                            try:
                                val = float(val)
                            except ValueError:
                                pass
                        record[col_name] = val
                    else:
                        record[col_name] = ""
                        
                records.append(record)
            
            return records
        finally:
            browser.close()

    def _scrape_indices_summary(self):
        """Cào VN-Index, VN30-Index và các chỉ số chính."""
        # Thực tế có thể lấy ngay trên header của bảng giá hoặc trang chủ
        # Ở đây ta giả lập lấy VN-Index và VN30-Index
        print("🔍 Đang lấy dữ liệu VN-Index và VN30-Index...")
        
        import platform
        if platform.system() == "Linux":
            d_path = "/usr/bin/chromedriver"
            e_args = ["--no-sandbox", "--disable-dev-shm-usage"]
        else:
            d_path = self.chromedriver_path
            e_args = []
            
        browser = ChromeController(driver_path=d_path, headless=True, extra_args=e_args)
        
        try:
            browser.begin()
            browser.open_new_tab(self.URL_MARKET, name='vietstock_main')
            browser.switch_to_tab('vietstock_main')
            
            # Selector cho VN-Index và VN30 (tùy thuộc vào site Vietstock cập nhật)
            # Giả định lấy từ các thẻ header
            res = []
            # Ví dụ: VN-Index
            vni_p = browser.get_text('//*[@id="vne-index-last"]') # Giả định id
            vni_c = browser.get_text('//*[@id="vne-index-change"]')
            
            if vni_p:
                res.append({
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "symbol": "VNINDEX",
                    "close": float(vni_p.replace(",", "")),
                    "change_pct": float(vni_c.replace("%", "").strip()),
                    "type": "INDEX"
                })
            
            return res
        except Exception as e:
            shot = browser.capture_error("indices_summary_err")
            if self.notifier and shot:
                self.notifier.send_photo(shot, caption=f"❌ <b>Lỗi Scraping Indices</b>\nChi tiết: {str(e)}")
            return [] # Mock hoặc bỏ qua nếu selector sai
        finally:
            browser.close()

    def _format_vol(self, vol):
        """Format khối lượng giao dịch linh hoạt (cp, K, Tr), giới hạn 3 chữ số trước thập phân."""
        if not vol: return "0 cp"
        
        if vol >= 999500: # Ngưỡng để 999.5K+ làm tròn thành 1.0Tr
            return f"{vol/1000000:.1f}Tr cp"
        elif vol >= 1000:
            return f"{vol/1000:.1f}K cp"
        else:
            return f"{vol:,.0f} cp"

    def get_report(self, session="MARKET_INTRADAY"):
        """Tạo báo cáo VN-Index dựa theo bản chất của bản tin (Opening vs Trading)."""
        vn30_stocks = self._scrape_vn30_data()
        
        # Lưu vào Google Sheet (Lưu liên tục nhưng lần chạy Afternoon sẽ là số liệu chốt ngày)
        if vn30_stocks:
            self.gs.update_financial_optimized("vn-index", vn30_stocks)
            
        if not vn30_stocks:
            return f"🇻🇳 <b>Thị trường Việt Nam ({session})</b>\n❌ Không lấy được dữ liệu."
            
        title = f"🇻🇳 <b>Thị trường Việt Nam ({session})</b>"
        report = f"{title}\n"
        
        # Tiền xử lý dữ liệu Khối ngoại và Khối lượng
        for s in vn30_stocks:
            f_buy = s.get('ForeignBuy', '')
            f_buy = float(f_buy) if f_buy != "" else 0
            f_sell = s.get('ForeignSell', '')
            f_sell = float(f_sell) if f_sell != "" else 0
            s['ForeignNet'] = f_buy - f_sell
            
            vol = s.get('TotalVol', '')
            s['TotalVol'] = float(vol) if vol != "" else 0

        # Phân loại logic theo bản chất bản tin
        is_opening = any(kw in session.upper() for kw in ["OPENING", "PRE_MARKET", "MORNING"])
        
        if is_opening:
            # 1. Sự kiện / Cảnh báo
            events = [s for s in vn30_stocks if s.get('Note') in ['event', 'warning']]
            if events:
                report += "\n⚠️ <b>Sự kiện / Cảnh báo:</b>\n<pre>"
                for s in events:
                    note_str = "Sắp có sự kiện" if s.get('Note') == 'event' else "Bị cảnh báo"
                    report += f"- {s['symbol']:<5}: {note_str}\n"
                report += "</pre>"
                
            # 2. Khối ngoại (Net Buy/Sell từ dữ liệu chốt phiên hôm qua)
            sorted_fn = sorted(vn30_stocks, key=lambda x: x['ForeignNet'], reverse=True)
            top_fb = [s for s in sorted_fn[:3] if s['ForeignNet'] > 0]
            top_fs = [s for s in sorted_fn[-3:] if s['ForeignNet'] < 0]
            top_fs = sorted(top_fs, key=lambda x: x['ForeignNet']) # sort ascending cho bán ròng
            
            if top_fb or top_fs:
                report += "\n📊 <b>Khối Ngoại hôm qua (Mua/Bán Ròng):</b>\n<pre>"
                if top_fb:
                    report += "📈 Top Mua:\n"
                    for s in top_fb:
                        report += f"   {s['symbol']:<4}: +{s['ForeignNet']:,.0f}\n"
                if top_fs:
                    report += "📉 Top Bán:\n"
                    for s in top_fs:
                        report += f"   {s['symbol']:<4}: {s['ForeignNet']:,.0f}\n"
                report += "</pre>"
                
        else: # Noon and Afternoon
            # 1. Kịch biên độ (Ceiling / Floor)
            ceilings = []
            floors = []
            for s in vn30_stocks:
                mp = s.get('MatchPrice', '')
                ceil = s.get('Ceiling', '')
                fl = s.get('Floor', '')
                if mp != "" and ceil != "" and float(mp) > 0 and float(mp) >= float(ceil):
                    ceilings.append(s)
                elif mp != "" and fl != "" and float(mp) > 0 and float(mp) <= float(fl):
                    floors.append(s)
            
            if ceilings or floors:
                report += "\n🚀 <b>Chạm Biên Độ:</b>\n<pre>"
                for s in ceilings:
                    vol_str = self._format_vol(s['TotalVol'])
                    report += f"- {s['symbol']:<5}: {s['MatchPrice']} (Trần) | Vol: {vol_str}\n"
                for s in floors:
                    vol_str = self._format_vol(s['TotalVol'])
                    report += f"- {s['symbol']:<5}: {s['MatchPrice']} (Sàn)  | Vol: {vol_str}\n"
                report += "</pre>"
            
            exclude_symbols = set([s['symbol'] for s in ceilings + floors])
            
            # 2. Biến động mạnh (Top 3 Tăng / Giảm) không trùng list kịch biên độ
            remaining_stocks = [s for s in vn30_stocks if s['symbol'] not in exclude_symbols]
            sorted_pct = sorted(remaining_stocks, key=lambda x: x['change_pct'], reverse=True)
            
            top_gainers = [s for s in sorted_pct if s['change_pct'] > 0][:3]
            top_losers = [s for s in sorted_pct if s['change_pct'] < 0][-3:]
            
            if top_gainers or top_losers:
                report += "\n🔥 <b>Biến Động Mạnh Nhất:</b>\n<pre>"
                report += f"{'Mã':<6} {'Giá':>6} {'1D':>7} {'1W':>5} {'1M':>4} {'1Q':>4} {'1Y':>4}\n"
                report += "-" * 40 + "\n"
                
                # Hàm helper in dòng
                def format_row(s):
                    return f"{s['symbol']:<6} {s['close']:>6.2f} {s['change_pct']:>+6.1f}% {'-':>4} {'-':>4} {'-':>4} {'-':>4}\n"
                
                for s in top_gainers:
                    report += format_row(s)
                if top_gainers and top_losers:
                    report += "...\n"
                for s in top_losers:
                    report += format_row(s)
                report += "</pre>"
            
            # 3. Top Thanh khoản (Không loại trừ, lấy Top 3 tuyệt đối trên toàn thị trường)
            sorted_vol = sorted(vn30_stocks, key=lambda x: x['TotalVol'], reverse=True)[:3]
            
            if sorted_vol:
                report += "\n🌊 <b>Top Thanh Khoản (Khối lượng):</b>\n<pre>"
                for s in sorted_vol:
                    vol_str = self._format_vol(s['TotalVol'])
                    report += f"- {s['symbol']:<5}: {vol_str:>10} ({s['change_pct']:>+4.1f}%)\n"
                report += "</pre>"
                
            # 4. Khối ngoại (Top 3 Mua/Bán Ròng)
            sorted_fn = sorted(vn30_stocks, key=lambda x: x['ForeignNet'], reverse=True)
            top_fb = [s for s in sorted_fn[:3] if s['ForeignNet'] > 0]
            top_fs = [s for s in sorted_fn[-3:] if s['ForeignNet'] < 0]
            top_fs = sorted(top_fs, key=lambda x: x['ForeignNet'])
            
            if top_fb or top_fs:
                report += "\n📊 <b>Khối Ngoại (Mua/Bán ròng):</b>\n<pre>"
                if top_fb:
                    report += "📈 Mua: " + ", ".join([f"{s['symbol']}(+{s['ForeignNet']:,.0f})" for s in top_fb]) + "\n"
                if top_fs:
                    report += "📉 Bán: " + ", ".join([f"{s['symbol']}({s['ForeignNet']:,.0f})" for s in top_fs]) + "\n"
                report += "</pre>"

        return report
