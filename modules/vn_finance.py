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
            
            # Đợi bảng giá xuất hiện (Thử nhiều selector cho chắc chắn)
            selectors = [
                '//*[@id="price-board-body"]',
                '//table[@id="price-board"]/tbody',
                '//div[@id="price-board-container"]//tbody',
                '//div[contains(@id, "price-board")]//tbody',
                '//tbody'
            ]
            
            found = False
            for sel in selectors:
                if browser.wait_xpath(sel, timeout=30):
                    found = True
                    target_xpath = sel
                    break
            
            if not found:
                print("❌ Timeout: Không tìm thấy selector bảng giá.")
                shot = browser.capture_error("vn30_timeout")
                if self.notifier and shot:
                    self.notifier.send_photo(shot, caption="❌ <b>Lỗi Scraping VN30</b>\nKhông tìm thấy bảng giá Vietstock (Timeout).")
                return []

            # Đợi dữ liệu load hoàn toàn (Check xem có ít nhất một mã CK nào đó chưa)
            # Thường là ACB hoặc các mã VN30 phổ biến
            data_loaded = False
            for _ in range(10): # Thử đợi thêm tối đa 10s
                raw_element = browser.get_xpath(target_xpath)
                if raw_element and "ACB" in raw_element.text:
                    data_loaded = True
                    break
                time.sleep(1)
            
            if not data_loaded:
                print("❌ Dữ liệu chưa kịp load hoặc không tìm thấy mã ACB.")
                shot = browser.capture_error("vn30_data_empty")
                if self.notifier and shot:
                    self.notifier.send_photo(shot, caption="❌ <b>Lỗi Scraping VN30</b>\nDữ liệu bảng giá trống hoặc chưa tải xong.")
                return []
                
            raw_text = raw_element.text
            raw_text = raw_text.strip()
            
            # Xử lý text thô: Vietstock có thể trả về newline giữa các cell hoặc space
            # Phân tách logic: Mỗi mã CK bắt đầu một record mới
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

            # -------------------------------------------------------------
            # NEW PARSING LOGIC: Ghép dòng linh hoạt (Phòng trường hợp mỗi cell là 1 line)
            # -------------------------------------------------------------
            
            # List các mã VN30 để làm mốc phân tách (nếu cần)
            # Hoặc đơn giản là mỗi mã CK có 3-4 ký tự in hoa
            # Hàm hỗ trợ parse number thông minh (Theo yêu cầu mới)
            def parse_number(p):
                # Lưu ý: p vẫn là chuỗi thô từ web
                p_clean = p.strip()
                if not p_clean or p_clean == '-': return '0'
                
                # Luật 1: Nếu là % (tính từ phải qua: %, số, dấu phân cách)
                if p_clean.endswith('%'):
                    # Ví dụ: "1.5%" hoặc "1,5%"
                    if len(p_clean) >= 3 and p_clean[-3] in ['.', ',']:
                        # Đây là dấu thập phân
                        val_str = p_clean[:-1].replace(',', '.') # Convert to standard float string
                        return val_str
                    else:
                        # Trường hợp % khác (vd: "15%") -> bỏ % lấy số
                        return p_clean.replace('%', '').replace(',', '.')
                
                # Luật 2: Các số liệu khác (Giá, KL)
                # "Bỏ hết dấu chấm và phẩy, sau đó nhân 10 sẽ ra giá trị đúng"
                val_raw = p_clean.replace('.', '').replace(',', '')
                try:
                    return str(float(val_raw) * 10)
                except ValueError:
                    return '0'

            def is_symbol(s):
                # Symbol có 3 chữ in hoa, có thể kèm * hoặc ** (vd: BID*, ACB**)
                return re.match(r'^[A-Z]{3}\**$', s)

            records = []
            current_symbol_tokens = []
            
            # Hàm xử lý data line cũ hoặc list tokens
            def build_record_from_tokens(tokens):
                if len(tokens) < 10: return None # Thiếu dữ liệu tối thiểu
                
                symbol_raw = tokens[0]
                symbol = re.sub(r"\*+", "", symbol_raw)
                mark = ""
                if symbol_raw.endswith("**"): mark = "warning"
                elif symbol_raw.endswith("*"): mark = "event"
                
                # Gom các tokens còn lại làm data
                # Nếu tokens[1] là một chuỗi dài (space separated), split nó ra
                all_data_points = []
                for t in tokens[1:]:
                    if " " in t:
                        all_data_points.extend(t.split(" "))
                    else:
                        all_data_points.append(t)
                
                # Parse all numbers
                parts = [parse_number(p) for p in all_data_points]
                
                # Map vào columns (Lấy chính xác theo index)
                # Symbol, Note là 2 cột đầu
                rec = [symbol, mark] + parts
                
                record = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "type": "VN30_STOCK",
                    "symbol": symbol,
                    "close": float(parts[9]) if len(parts) > 9 else 0,        # MatchPrice
                    "change": float(parts[11]) if len(parts) > 11 else 0,     # Change
                    "change_pct": float(parts[12]) if len(parts) > 12 else 0, # ChangePct
                    "volume": int(float(parts[19])) if len(parts) > 19 else 0 # TotalVol
                }

                # Link all defined columns
                for idx, col_name in enumerate(columns):
                    if idx < len(rec):
                        val = rec[idx]
                        if col_name not in ["Symbol", "Note"] and val:
                            try: val = float(val)
                            except ValueError: pass
                        record[col_name] = val
                    else:
                        record[col_name] = ""
                return record

            # Gom nhóm tokens theo Symbol
            i = 0
            while i < len(lines):
                token = lines[i]
                if is_symbol(token):
                    # Nếu đang có dở dang symbol trước đó, build nó
                    if current_symbol_tokens:
                        res = build_record_from_tokens(current_symbol_tokens)
                        if res: records.append(res)
                    current_symbol_tokens = [token]
                else:
                    current_symbol_tokens.append(token)
                i += 1
            
            # Đừng quên cái cuối cùng
            if current_symbol_tokens:
                res = build_record_from_tokens(current_symbol_tokens)
                if res: records.append(res)
            
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
            res = []
            
            # 1. VN-Index
            vni_p = browser.get_text('//*[@id="vne-index-last"]')
            vni_c = browser.get_text('//*[@id="vne-index-change"]')
            
            if vni_p:
                res.append({
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "symbol": "VNINDEX",
                    "close": float(vni_p.replace(",", "")),
                    "change_pct": float(vni_c.split("(")[-1].replace(")", "").replace("%", "").strip()) if "(" in vni_c else 0,
                    "type": "INDEX"
                })

            # 2. VN30-Index
            vn30_p = browser.get_text('//*[@id="vne-vn30-index-last"]')
            vn30_c = browser.get_text('//*[@id="vne-vn30-index-change"]')

            if vn30_p:
                res.append({
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "symbol": "VN30",
                    "close": float(vn30_p.replace(",", "")),
                    "change_pct": float(vn30_c.split("(")[-1].replace(")", "").replace("%", "").strip()) if "(" in vn30_c else 0,
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

    def _format_price(self, price_vnd):
        """Hiển thị giá theo đơn vị nghìn (k) (vd: 27500 -> 27.5k)."""
        if not price_vnd: return "0"
        return f"{price_vnd/1000:,.2f}k".rstrip('0').rstrip('.') + 'k'

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
                    price_str = self._format_price(s['close'])
                    return f"{s['symbol']:<6} {price_str:>7} {s['change_pct']:>+6.1f}% {'-':>4} {'-':>4} {'-':>4} {'-':>4}\n"
                
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
