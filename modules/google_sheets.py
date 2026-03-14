import os
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd

class GoogleSheetManager:
    """
    Quản lý kết nối và tương tác với Google Sheets.
    """
    def __init__(self, credential_file, sheet_key):
        self.credential_file = credential_file
        self.sheet_key = sheet_key
        self.client = None
        self.book = None
        self.sheets_cache = {}
        self._connect()

    def _connect(self):
        """Kết nối tới Google Sheets API dùng service account."""
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file(self.credential_file, scopes=scope)
        self.client = gspread.authorize(creds)
        self.book = self.client.open_by_key(self.sheet_key)
        print("✅ Đã kết nối tới Google Sheets")

    def get_sheet(self, sheetname):
        """Lấy worksheet theo tên, có cơ chế cache và reconnect."""
        try:
            if sheetname not in self.sheets_cache:
                self.sheets_cache[sheetname] = self.book.worksheet(sheetname)
            return self.sheets_cache[sheetname]
        except Exception:
            print("⚠️ Đang kết nối lại Google...")
            self._connect()
            self.sheets_cache = {}
            return self.get_sheet(sheetname)

    def get_all_records(self, sheetname):
        """Lấy toàn bộ dữ liệu từ một sheet dưới dạng danh sách dict."""
        sheet = self.get_sheet(sheetname)
        return sheet.get_all_records()

    def update_financial_optimized(self, sheetname, dict_rows):
        """Cập nhật dữ liệu tài chính (ghi đè nếu trùng ngày + symbol, hoặc thêm mới)."""
        sheet = self.get_sheet(sheetname)
        all_records = sheet.get_all_records()
        df_sheet = pd.DataFrame(all_records)
        headers = sheet.row_values(1)

        for new_row in dict_rows:
            if not df_sheet.empty:
                condition = (df_sheet["date"] == new_row["date"]) & (df_sheet["symbol"] == new_row["symbol"])
                match = df_sheet[condition]
            else:
                match = pd.DataFrame()
            
            ordered_row = [new_row.get(col, "") for col in headers]

            if match.empty:
                sheet.append_row(ordered_row)
                print(f"➕ Thêm mới: {new_row['date']} - {new_row['symbol']}")
            else:
                last_record = match.iloc[-1]
                changed = False
                cols_to_check = ["open", "high", "low", "close", "volume"]
                for col in cols_to_check:
                    if col in new_row and float(new_row[col]) != float(last_record.get(col, 0)):
                        changed = True
                        break
                
                if changed:
                    row_number = match.index[-1] + 2
                    last_col_letter = gspread.utils.rowcol_to_a1(1, len(headers))[:-1]
                    sheet.update(f"A{row_number}:{last_col_letter}{row_number}", [ordered_row])

    def append_rows(self, sheetname, dict_rows):
        """Thêm các hàng mới vào sheet (không kiểm tra trùng)."""
        sheet = self.get_sheet(sheetname)
        headers = sheet.row_values(1)
        rows = [[data.get(col, "") for col in headers] for data in dict_rows]
        sheet.append_rows(rows)
        print(f"✅ Đã thêm {len(rows)} hàng vào {sheetname}")

    def update_cell_by_match(self, sheetname, match_col, match_val, update_col, new_val):
        """Tìm hàng có match_col = match_val và cập nhật update_col = new_val."""
        sheet = self.get_sheet(sheetname)
        records = sheet.get_all_records()
        headers = sheet.row_values(1)
        
        try:
            target_col_idx = headers.index(update_col) + 1
            for i, row in enumerate(records):
                if str(row.get(match_col)) == str(match_val):
                    row_num = i + 2
                    sheet.update_cell(row_num, target_col_idx, new_val)
                    return True
        except ValueError:
            print(f"❌ Không tìm thấy cột: {update_col}")
        return False
