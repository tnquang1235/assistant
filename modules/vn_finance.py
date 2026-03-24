import re
import pandas as pd
import time
from datetime import datetime
from scc.controller import ChromeController

class VNFinanceModule:
    """
    Module xử lý dữ liệu chứng khoán Việt Nam (VN-Index, VN30, Ngành).
    Phiên bản: 1.4.0 (Refactored for maintainability)
    """

    # =========================================================
    # BẢNG CẤU HÌNH XPATHS (Dễ dàng điều chỉnh khi Web đổi cấu trúc)
    # =========================================================
    
    # Thời gian chờ (giây) sau khi tải URL VN30 để đảm bảo dữ liệu hiển thị xong
    VN30_PAGE_LOAD_WAIT = 10
    
    # 1. Cấu hình bảng giá VN30 (Chỉ dùng xpath này, không tìm cấu trúc khác)
    VN30_TABLE_XPATH = '//tbody[@id="price-board-body"]'

    # 2. Cấu hình các chỉ số thị trường (Dùng trong _scrape_indices_summary)
    # Structural XPaths (Targeting by position in the indices bar)
    INDEX_CONFIG = {
        "VNINDEX": {
            "label": "VN-INDEX",
            "val_xpath": '(//div[@id="header-indices"]//div[contains(@class, "index-item")])[1]//div[contains(@class, "index-price")]',
            "chg_xpath": '(//div[@id="header-indices"]//div[contains(@class, "index-item")])[1]//div[contains(@class, "index-change")]'
        },
        "VN30": {
            "label": "VN30-INDEX",
            "val_xpath": '(//div[@id="header-indices"]//div[contains(@class, "index-item")])[4]//div[contains(@class, "index-price")]',
            "chg_xpath": '(//div[@id="header-indices"]//div[contains(@class, "index-item")])[4]//div[contains(@class, "index-change")]'
        }
    }

    URLs = {
        "VN30": "https://banggia.vietstock.vn/bang-gia/vn30"
    }

    # Danh sách cột chuẩn hóa cho Google Sheets
    COLUMNS_VN_INDEX = [
        "Symbol", "Note",
        "RefPrice", "Ceiling", "Floor",
        "BidPrice3", "BidVol3", "BidPrice2", "BidVol2", "BidPrice1", "BidVol1",
        "MatchPrice", "MatchVol", "Change", "ChangePct",
        "AskPrice1", "AskVol1", "AskPrice2", "AskVol2", "AskPrice3", "AskVol3",
        "TotalVol", "High", "Low", "Avg",
        "ForeignBuy", "ForeignSell"
    ]

    # =========================================================

    def __init__(self, google_manager, notifier=None, chromedriver_path="./chromedriver.exe"):
        self.gs = google_manager
        self.notifier = notifier
        self.chromedriver_path = chromedriver_path

    @staticmethod
    def parse_number(p, is_vol=False):
        """Hàm xử lý số liệu theo quy tắc 10x và xử lý %."""
        p_clean = p.strip()
        if not p_clean or p_clean == '-': return '0'
        
        # Luật 1: Nếu là % (tính từ phải qua: %, số, dấu phân cách)
        if p_clean.endswith('%'):
            if len(p_clean) >= 3 and p_clean[-3] in ['.', ',']:
                return p_clean[:-1].replace(',', '.') # Convert sang float chuẩn
            return p_clean.replace('%', '').replace(',', '.')
        
        # Luật 2: Bỏ hết dấu chấm/phẩy và nhân 10
        val_raw = p_clean.replace('.', '').replace(',', '')
        try:
            if is_vol: # Volume doesn't need *10
                return str(float(val_raw))
            return str(float(val_raw) * 10)
        except ValueError:
            return '0'

    def _scrape_vn30_data(self, browser):
        """Cào dữ liệu chi tiết bảng giá VN30."""
        print("[INFO] Scraping VN30 logs...")
        
        try:
            browser.open_new_tab(self.URLs["VN30"], name='vietstock_vn30')
            browser.switch_to_tab('vietstock_vn30')
            
            # Đợi load dữ liệu
            print(f"[INFO] Waiting {self.VN30_PAGE_LOAD_WAIT}s for stock data to sync...")
            time.sleep(self.VN30_PAGE_LOAD_WAIT)
            browser.wait_xpath('//*[@id="header-container"]/div[@class="logo"]')

            # Kiểm tra web đã load chưa bằng việc đếm tr có đủ 30 chưa
            print(f"[STEP 1/2] Waiting for actual row data in {self.VN30_TABLE_XPATH} (Expected: 30)...")
            data_loaded = False
            row_count = 0
            for _ in range(15):
                row_count = browser.count_xpath(f"{self.VN30_TABLE_XPATH}/tr")
                if row_count >= 30:
                    data_loaded = True
                    print(f"   [OK] Detected {row_count} data rows.")
                    break
                time.sleep(1)
            
            if not data_loaded:
                print(f"[ERROR] Data empty or rows not enough. Last count: {row_count}")
                shot = browser.capture_error("vn30_load_error")
                if self.notifier:
                    self.notifier.send(
                        f"❌ <b>Scraping VN30 Error</b>\n"
                        f"<b>Step:</b> Row Count Check\n"
                        f"<b>Detail:</b> Chỉ tìm thấy {row_count} dòng (yêu cầu >= 30) trong <code>{self.VN30_TABLE_XPATH}</code>."
                    )
                    # Gửi ảnh chụp màn hình bị lỗi
                    if shot:
                        try:
                            self.notifier.send_photo(shot, caption="📸 Màn hình lỗi VN30")
                        except AttributeError:
                            self.notifier.send(f"⚠️ Ảnh lỗi đã được lưu tại: {shot}")
                            
                return []
                
            # Phân tích dữ liệu bằng cách chụp 1 lần duy nhất (Atomic Snapshot)
            print("[STEP 2/2] Parsing table via outerHTML Snapshot and Raw data-value...")
            table_element = browser.get_xpath(self.VN30_TABLE_XPATH)
            table_html = table_element.get_attribute("outerHTML")
            
            records = []
            
            # Dùng regex để tìm tất cả các block <tr>
            tr_blocks = re.finditer(r'<tr\b([^>]*)>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)
            
            def get_val(html_content, col_prefix, row_number):
                m = re.search(fr'id="{col_prefix}-{row_number}"[^>]*data-value="([^"]+)"', html_content)
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        pass
                return 0.0
            
            for match in tr_blocks:
                tr_attrs = match.group(1)
                tr_content = match.group(2)
                
                # Bỏ qua dòng bị ẩn
                if "hidden" in tr_attrs.lower():
                    continue
                    
                # Lấy Mã CK (Symbol)
                symbol_match = re.search(r'data-symbol="([^"]+)"', tr_attrs)
                if not symbol_match:
                    continue
                symbol = symbol_match.group(1).replace('*', '').strip()
                if not symbol or len(symbol) > 10:
                    continue

                # Lấy ID của dòng để tham chiếu giá trị bên trong
                row_id_match = re.search(r'id="row-(\d+)"', tr_attrs)
                if not row_id_match:
                    continue
                row_id = row_id_match.group(1)
                
                # Fetch essential fields
                price_val = get_val(tr_content, 'lastP', row_id)
                change_pct_val = get_val(tr_content, 'lastPC', row_id)
                tVol_val = get_val(tr_content, 'tVol', row_id)
                foreign_buy = get_val(tr_content, 'foreignBV', row_id)
                foreign_sell = get_val(tr_content, 'foreignOV', row_id)
                change_val = get_val(tr_content, 'lastC', row_id)

                # Map fully perfectly to vn_index_template.csv columns
                record = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "type": "STOCK",
                    "symbol": symbol,
                    "close": price_val,
                    "change": change_val,
                    "change_pct": round(change_pct_val, 2),
                    "volume": tVol_val,  
                    "RefPrice": get_val(tr_content, 'basicP', row_id),
                    "Ceiling": get_val(tr_content, 'ceilP', row_id),
                    "Floor": get_val(tr_content, 'floorP', row_id),
                    "MatchPrice": price_val,
                    "MatchVol": get_val(tr_content, 'lastV', row_id),
                    "Change": change_val,
                    "ChangePct": round(change_pct_val, 2),
                    "High": get_val(tr_content, 'highP', row_id),
                    "Low": get_val(tr_content, 'lowP', row_id),
                    "Avg": get_val(tr_content, 'averageP', row_id),
                    "ForeignBuy": foreign_buy,
                    "ForeignSell": foreign_sell,
                    "ForeignNet": foreign_buy - foreign_sell,
                    "BidPrice3": get_val(tr_content, 'bP3', row_id),
                    "BidVol3": get_val(tr_content, 'bV3', row_id),
                    "BidPrice2": get_val(tr_content, 'bP2', row_id),
                    "BidVol2": get_val(tr_content, 'bV2', row_id),
                    "BidPrice1": get_val(tr_content, 'bP1', row_id),
                    "BidVol1": get_val(tr_content, 'bV1', row_id),
                    "AskPrice1": get_val(tr_content, 'oP1', row_id),
                    "AskVol1": get_val(tr_content, 'oV1', row_id),
                    "AskPrice2": get_val(tr_content, 'oP2', row_id),
                    "AskVol2": get_val(tr_content, 'oV2', row_id),
                    "AskPrice3": get_val(tr_content, 'oP3', row_id),
                    "AskVol3": get_val(tr_content, 'oV3', row_id),
                    "Note": "VN30"
                }
                records.append(record)
            
            print(f"[INFO] Successfully parsed {len(records)} full multi-column records using Snapshot.")
            return records
            
        except Exception as e:
            print(f"[ERROR] Exception during VN30 scraping: {e}")
            return []

    def _build_stock_record(self, tokens):
        """Chuyển tokens thành record hoàn chỉnh."""
        # This function is no longer used with the new parsing logic in _scrape_vn30_data
        # Keeping it for now in case of future refactoring or if the old method is needed.
        if len(tokens) < 10: return None
        
        symbol_raw = tokens[0]
        symbol = re.sub(r"\*+", "", symbol_raw)
        
        # Note phản ánh bản chất nhóm VN30 và cảnh báo
        mark = "VN30"
        if symbol_raw.endswith("**"): mark += " [Warning]"
        elif symbol_raw.endswith("*"): mark += " [Event]"
        
        all_data = []
        for t in tokens[1:]:
            all_data.extend(t.split(" "))
            
        parts = [self.parse_number(p) for p in all_data]
        
        record = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "type": "STOCK",  # Chuẩn hóa type là STOCK
            "symbol": symbol,
            "Note": mark,
            "close": float(parts[9]) if len(parts) > 9 else 0,
            "change_pct": float(parts[12]) if len(parts) > 12 else 0,
            "total_vol": float(parts[19]) if len(parts) > 19 else 0
        }

        # Map vào các cột cho Sheets
        row_data = [symbol, mark] + parts
        for i, col in enumerate(self.COLUMNS_VN_INDEX):
            if i < len(row_data):
                val = row_data[i]
                try: val = float(val) if i >= 2 else val
                except: pass
                record[col] = val
        
        return record

    def _scrape_indices_summary(self, browser):
        """Lấy tóm tắt các chỉ số chính (VN-Index, VN30...)."""
        print("[INFO] Scraping Market Indices...")
        indices_data = []
        
        # Đợi SignalR đổ dữ liệu (Indices cũng cần sync)
        print("[INFO] Waiting for SignalR indices sync...")
        
        for key, cfg in self.INDEX_CONFIG.items():
            try:
                # Debug Check
                print(f"   [DEBUG] ID header-indices in source: {'header-indices' in browser.browser.page_source}")
                container_xpath = f'(//div[@id="header-indices"]//div[contains(@class, "index-item")])[{"1" if key=="VNINDEX" else "4"}]'
                container = browser.get_xpath(container_xpath)
                if container:
                    print(f"   [DEBUG] Found container for {key}. HTML: {container.get_attribute('outerHTML')[:100]}...")
                else:
                    print(f"   [DEBUG] Container NOT FOUND for {key} at {container_xpath}")

                # Optimized: Wait once for the value to appear
                if browser.wait_xpath(cfg["val_xpath"], timeout=15):
                    val_text = browser.get_text(cfg["val_xpath"])
                    chg_text = browser.get_text(cfg["chg_xpath"])
                else:
                    val_text = None
                    chg_text = None
                
                if val_text and any(c.isdigit() for c in val_text):
                    p_val = float(val_text.strip().replace(",", ""))
                    c_pct = 0.0
                    if chg_text and "(" in chg_text:
                        c_pct_str = chg_text.split("(")[-1].replace(")", "").replace("%", "").strip()
                        c_pct = float(c_pct_str.replace(",", "."))
                    
                    indices_data.append({
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "symbol": key,
                        "type": "INDEX",
                        "Note": "Market Indicator",
                        "close": p_val,
                        "change_pct": c_pct
                    })
                    print(f"   [INDEX] {cfg['label']}: {val_text}")
                else:
                    print(f"   [INDEX] {cfg['label']}... [TIMEOUT OR NO DATA]")
            except Exception as e:
                print(f"   [INDEX] Error {key}: {e}")
        
        return indices_data

    def _format_price(self, price_raw):
        """Dinh dang gia VND sang k (viu 27,500 -> 27.5k)."""
        try:
            val = float(price_raw)
            if val == 0: return "0"
            k_val = val / 1000
            if k_val >= 10:
                return f"{k_val:,.1f}k"
            else:
                return f"{k_val:,.2f}k"
        except: return str(price_raw)

    def get_report(self, session="MARKET_SNAPSHOT"):
        """Tạo báo cáo tổng hợp. Toi uu: dung chung 1 browser session."""
        import platform
        d_path = "/usr/bin/chromedriver" if platform.system() == "Linux" else self.chromedriver_path
        e_args = ["--no-sandbox", "--disable-dev-shm-usage"] if platform.system() == "Linux" else []
        
        browser = ChromeController(driver_path=d_path, headless=True, extra_args=e_args)
        all_indicators = []
        all_stocks = []

        try:
            browser.begin()
            # 1. Crawling VN30 Details
            # browser.open_new_tab(self.URLs["VN30"], name='vn30_board')
            # browser.switch_to_tab('vn30_board')
            all_stocks = self._scrape_vn30_data(browser)

            # Update Google Sheets
            if all_indicators: self.gs.update_financial_optimized("vn-index", all_indicators)
            if all_stocks: self.gs.update_financial_optimized("vn-index", all_stocks)

        except Exception as e:
            print(f"[ERROR] Global VN-Index Scraping Error: {e}")
            if self.notifier:
                self.notifier.send(f"❌ <b>Fatal VN-Index Error</b>\n{str(e)[:100]}")
        finally:
            browser.close()

        if not all_indicators and not all_stocks:
            return "------------------------------\n<b>Vietnam Market</b>\n[ERROR] Fetching failed.      \n------------------------------"

        # Format Telegram Report
        report = f"🇻🇳 <b>Vietnam Market ({session})</b>\n<pre>"
        if all_indicators:
            for idx in all_indicators:
                icon = "🟢" if idx['change_pct'] >= 0 else "🔴"
                report += f"{icon} {idx['symbol']:<8} {idx['close']:>8,.2f} ({idx['change_pct']:>+5.2f}%)\n"
            report += "\n"
        
        if all_stocks:
            report += "📈 <b>VN30 - Movers (1D)</b>\n"
            # Top 3 tang manh va 3 giam manh
            sorted_stocks = sorted(all_stocks, key=lambda x: x['change_pct'], reverse=True)
            movers = sorted_stocks[:3]
            if len(sorted_stocks) > 6: movers += sorted_stocks[-3:]
            
            for s in movers:
                p_fmt = self._format_price(s['close'])
                report += f"{s['symbol']:<6} {p_fmt:>8} {s['change_pct']:>+7.2f}%\n"
        
        report += "</pre>"
        return report
