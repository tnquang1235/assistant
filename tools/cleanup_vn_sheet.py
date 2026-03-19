import os
import pandas as pd
from modules.google_sheets import GoogleSheetManager
from config import settings

def cleanup_vn_index_sheet():
    print("[CLEANUP] Starting cleanup for 'vn-index' sheet...")
    gs = GoogleSheetManager(settings.GOOGLE_CREDENTIAL_FILE, settings.VN_FINANCE_SHEET_ID)
    sheet_name = "vn-index"
    
    try:
        sheet = gs.get_sheet(sheet_name)
        all_records = sheet.get_all_records()
        if not all_records:
            print("[ERROR] No records found in sheet.")
            return

        df = pd.DataFrame(all_records)
        
        # 1. Consolidate Duplicate Columns (Case-insensitive)
        # Find unique list of lowercased headers
        all_cols = list(df.columns)
        unique_cols_map = {} # lower -> [Original names]
        for c in all_cols:
            lower_c = c.lower()
            if lower_c not in unique_cols_map:
                unique_cols_map[lower_c] = [c]
            else:
                unique_cols_map[lower_c].append(c)

        # Merge contents: if multiple original columns exist, combine them
        new_df = pd.DataFrame()
        for lower_c, originals in unique_cols_map.items():
            # Use the first one as preferred name or standardize
            preferred_name = originals[0] 
            # If there's one that matches our preferred naming convention, use it
            if lower_c == "symbol": preferred_name = "symbol"
            if lower_c == "matchprice": preferred_name = "MatchPrice"
            
            # Combine content: first non-empty value
            combined = df[originals[0]].fillna('')
            for other in originals[1:]:
                combined = combined.mask(combined == '', df[other].fillna(''))
            
            new_df[preferred_name] = combined

        # 2. Standardize Column Order
        preferred_order = [
            "date", "timestamp", "type", "symbol", "close", "change", "change_pct", "volume", "ForeignNet",
            "RefPrice", "Ceiling", "Floor", "MatchPrice", "MatchVol", "Change", "ChangePct",
            "High", "Low", "Avg", "ForeignBuy", "ForeignSell",
            "BidPrice1", "BidVol1", "BidPrice2", "BidVol2", "BidPrice3", "BidVol3",
            "AskPrice1", "AskVol1", "AskPrice2", "AskVol2", "AskPrice3", "AskVol3", "Note"
        ]
        
        # Filter only existing ones from preferred, then add remaining
        final_cols = [c for c in preferred_order if c in new_df.columns]
        remaining = [c for c in new_df.columns if c not in final_cols]
        final_cols.extend(remaining)
        
        new_df = new_df[final_cols]

        # 3. Update the sheet (Write back all)
        # Clear sheet first or update range
        data = [new_df.columns.tolist()] + new_df.values.tolist()
        
        # Determine range (e.g. A1:Z100)
        from gspread.utils import rowcol_to_a1
        last_col = rowcol_to_a1(1, len(final_cols))[:-1]
        last_row = len(data)
        
        print(f"[PROCESS] Updating sheet with {len(final_cols)} columns and {last_row} rows...")
        sheet.clear()
        sheet.update(f"A1:{last_col}{last_row}", data)
        print("[SUCCESS] Cleanup and Reorganization complete!")

    except Exception as e:
        print(f"[ERROR] during cleanup: {e}")

if __name__ == "__main__":
    cleanup_vn_index_sheet()
