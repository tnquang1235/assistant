import os
import re
import sys
import time
from datetime import datetime
from scc.controller import ChromeController
from modules.vn_finance import VNFinanceModule

# Mock GS only for logging
class MockGS:
    def update_financial_optimized(self, sheet_name, data):
        print(f"   [GS-MOCK] Data would be sent to '{sheet_name}' ({len(data)} rows)")

def run_test():
    print("=" * 50)
    print(f"DIAGNOSTIC TEST: VIETSTOCK SCRAPING ({datetime.now()})")
    print("=" * 50)
    
    # Initialize module (Controller will handle path resolution)
    vn = VNFinanceModule(MockGS())
    
    # We create controller without explicit path to use its internal search/cache
    browser = ChromeController(headless=True)
    actual_path = browser.driver_path # Resolved path
    
    print(f"[INFO] Using Chromedriver at: {actual_path}")
    
    try:
        browser.begin()
        
        # [STEP 1] Testing Index Summary
        print("\n[STEP 1] Testing Index Summary Scraping (VN-Index, VN30)...")
        browser.open_new_tab(vn.URLs["MARKET"], name='test_m')
        browser.switch_to_tab('test_m')
        print("   [INFO] Waiting 10s for page navigation...")
        time.sleep(10)
        indices = vn._scrape_indices_summary(browser)
        if indices:
            print(f"[OK] Successfully fetched {len(indices)} indices.")
        else:
            print("[ERROR] Failed to fetch indices.")
            browser.screenshot("test_fail_indices.png")
            print("   [INFO] Saved screenshot to logs/screenshots/test_fail_indices.png")

        # [STEP 2] Testing Detail VN30
        print("\n[STEP 2] Testing Details VN30 Stock Scraping...")
        browser.open_new_tab(vn.URLs["VN30"], name='test_v')
        browser.switch_to_tab('test_v')
        print("   [INFO] Waiting 10s for page navigation...")
        time.sleep(10)
        stocks = vn._scrape_vn30_data(browser)
        if stocks:
            print(f"[OK] Detected {len(stocks)} data rows correctly.")
        else:
            print("[ERROR] Failed to fetch stock table.")

        # [STEP 3] Testing Full Report Format
        print("\n[STEP 3] Testing Telegram Report Generation...")
        # Note: This will re-run the whole flow internally as a black-box test
        report = vn.get_report(session="DIAGNOSTIC_RUN")
        print("-" * 30)
        # Filter out potential unicode in report for console safety
        clean_report = report.encode('ascii', 'ignore').decode('ascii')
        print(clean_report)
        print("-" * 30)
        
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Test crashed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        browser.close()
        print("\n[DONE] Diagnostic completed.")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        # Final fallback for errors to avoid encoding crash
        try:
            print(f"\n[FATAL] Error occurred during test: {str(e)}")
        except:
             print("\n[FATAL] Error occurred, could not print details due to encoding.")
        import traceback
        traceback.print_exc()
