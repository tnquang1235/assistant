import os
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd

class GoogleSheetManager:
    """
    Quản lý kết nối và tương tác với Google Sheets.
    """
    def __init__(self, credential_file, sheet_key, notifier=None):
        self.credential_file = credential_file
        self.sheet_key = sheet_key
        self.notifier = notifier
        self.client = None
        self.book = None
        self.sheets_cache = {}
        self._connect()

    def _safe_api_call(self, func, *args, **kwargs):
        """Hàm bọc bảo vệ các lệnh gọi API với cơ chế Retry khi gặp lỗi Quota (429)."""
        import time
        from gspread.exceptions import APIError
        
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except APIError as e:
                if "429" in str(e) and attempt < max_retries:
                    wait_time = 65 # Chờ hơn 1 phút để reset quota
                    msg = f"[WARN] Google API Quota Exceeded. Waiting {wait_time}s to retry (Attempt {attempt+1}/{max_retries})..."
                    print(msg)
                    if self.notifier and attempt == 0:
                        self.notifier.send("Google Sheets API Busy. System is waiting to retry...")
                    time.sleep(wait_time)
                else:
                    err_msg = f"[ERROR] Google Sheet Error: {e}"
                    print(err_msg)
                    if self.notifier:
                        self.notifier.send(f"Warning: Cannot update Google Sheets.\nError: {str(e)[:100]}...\nPlease check manually.")
                    return None
            except Exception as e:
                print(f"[ERROR] System error during Sheets call: {e}")
                return None

    def _connect(self):
        """Kết nối tới Google Sheets API dùng service account."""
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file(self.credential_file, scopes=scope)
        self.client = gspread.authorize(creds)
        self.book = self.client.open_by_key(self.sheet_key)
        print("[SUCCESS] Connected to Google Sheets")

    def get_sheet(self, sheetname):
        """Lấy worksheet theo tên, có cơ chế cache và reconnect."""
        try:
            if sheetname not in self.sheets_cache:
                self.sheets_cache[sheetname] = self.book.worksheet(sheetname)
            return self.sheets_cache[sheetname]
        except Exception:
            print("[INFO] Reconnecting to Google...")
            self._connect()
            self.sheets_cache = {}
            return self.get_sheet(sheetname)

    def get_all_records(self, sheetname):
        """Lấy toàn bộ dữ liệu từ một sheet dưới dạng danh sách dict."""
        sheet = self.get_sheet(sheetname)
        return self._safe_api_call(sheet.get_all_records)

    def update_financial_optimized(self, sheetname, dict_rows):
        """Cơ chế Ghi đè theo khối (Block Overwrite) thông minh để tiết kiệm API Quota."""
        if not dict_rows: return
        
        sheet = self.get_sheet(sheetname)
        all_records = self._safe_api_call(sheet.get_all_records)
        if all_records is None: return
        
        headers = self._safe_api_call(sheet.row_values, 1)
        if headers is None: return

        # 1. Tự động bổ sung cột mới nếu cần (Xử lý không phân biệt hoa thường)
        headers_lower = [h.lower() for h in headers]
        new_keys = []
        for row in dict_rows:
            for k in row.keys():
                k_lower = k.lower()
                if k_lower not in headers_lower and k_lower not in [nk.lower() for nk in new_keys]:
                    new_keys.append(k)
        
        if new_keys:
            headers.extend(new_keys)
            last_col_letter = gspread.utils.rowcol_to_a1(1, len(headers))[:-1]
            self._safe_api_call(sheet.update, f"A1:{last_col_letter}1", [headers])
            headers_lower = [h.lower() for h in headers] # Update lower cache

        # 2. Xu ly logic Cap nhat theo khoi (Block Update) x Them moi (Append)
        df_sheet = pd.DataFrame(all_records).astype(object)
        rows_to_append = []
        
        # Lưu vết các hàng bị thay đổi để tìm dải Row Min-Max
        updated_indices = []

        for new_row in dict_rows:
            match = pd.DataFrame()
            if not df_sheet.empty:
                condition = (df_sheet["date"] == new_row["date"]) & (df_sheet["symbol"] == new_row["symbol"])
                match = df_sheet[condition]
            
            # Helper to find value in dict with Case-Insensitive key
            def get_case_insensitive(d, key):
                k_low = key.lower()
                for k, v in d.items():
                    if k.lower() == k_low: return v
                return ""

            ordered_row = [get_case_insensitive(new_row, col) for col in headers]

            if match.empty:
                rows_to_append.append(ordered_row)
            else:
                idx = match.index[-1]
                last_record = match.iloc[-1]
                
                # So sánh giá trị để quyết định có ghi đè không
                changed = False
                for col in ["close", "volume"]:
                    if col in new_row:
                        try:
                            v_new = float(str(new_row[col]).replace('.', '').replace(',', '.'))
                            v_old = float(str(last_record.get(col, 0)).replace('.', '').replace(',', '.'))
                            if v_new != v_old: changed = True; break
                        except:
                            if str(new_row[col]) != str(last_record.get(col, 0)): changed = True; break
                
                if changed:
                    # Cập nhật vào DataFrame nội bộ
                    for col_idx, col_name in enumerate(headers):
                        df_sheet.at[idx, col_name] = ordered_row[col_idx]
                    updated_indices.append(idx)

        # 3. Thực thi Ghi đè theo Khối (Single Range Update)
        if updated_indices:
            min_idx = min(updated_indices)
            max_idx = max(updated_indices)
            # Row thực tế trên Sheet = index + 2
            start_row = min_idx + 2
            end_row = max_idx + 2
            
            # Trích xuất toàn bộ khối dữ liệu từ min tới max (bao gồm cả những hàng không đổi ở giữa)
            # Cách này giúp gom 30 lần ghi thành 1 lần duy nhất
            block_data = df_sheet.iloc[min_idx:max_idx+1].values.tolist()
            last_col_letter = gspread.utils.rowcol_to_a1(1, len(headers))[:-1]
            range_label = f"A{start_row}:{last_col_letter}{end_row}"
            
            self._safe_api_call(sheet.update, range_label, block_data)
            print(f"[REPLACE] Block Overwrite thanh cong: {range_label} ({len(block_data)} hang)")

        # 4. Thuc thi Them moi hang loat
        if rows_to_append:
            self._safe_api_call(sheet.append_rows, rows_to_append)
            print(f"[APPEND] Them moi hang loat thanh cong: {len(rows_to_append)} ma.")

    def append_rows(self, sheetname, dict_rows):
        """Them cac hang moi vao sheet (khong kiem tra trung)."""
        sheet = self.get_sheet(sheetname)
        headers = self._safe_api_call(sheet.row_values, 1)
        if headers is None: return
        
        rows = [[data.get(col, "") for col in headers] for data in dict_rows]
        self._safe_api_call(sheet.append_rows, rows)
        print(f"[APPEND] Da them {len(rows)} hang vao {sheetname}")

    def update_cell_by_match(self, sheetname, match_col, match_val, update_col, new_val):
        """Tìm hàng có match_col = match_val và cập nhật update_col = new_val."""
        sheet = self.get_sheet(sheetname)
        all_records = self.get_all_records(sheetname)
        if all_records is None: return False
        
        headers = self._safe_api_call(sheet.row_values, 1)
        if headers is None: return False
        
        try:
            target_col_idx = headers.index(update_col) + 1
            for i, row in enumerate(all_records):
                if str(row.get(match_col)) == str(match_val):
                    row_num = i + 2
                    self._safe_api_call(sheet.update_cell, row_num, target_col_idx, new_val)
                    return True
        except ValueError:
            print(f"[ERROR] Khong tim thay cot: {update_col}")
        return False
