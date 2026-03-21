import os
import json
import time
import logging
from datetime import datetime
from typing import Optional, List, Any

# import pymsgbox (Chuyển sang nạp chậm để hỗ trợ Headless/Linux)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from .constants import VERSION, LAST_UPDATED, SPECIAL_KEYS
from .helpers import logger, retry, decode_chrome_file_icon_url
from .models import DownloadItem

class ChromeController:
    """
    Lớp chính điều khiển Chrome qua Selenium.
    Version: {VERSION}
    """
    VERSION = VERSION
    LAST_UPDATED = LAST_UPDATED

    def __init__(
            self, 
            driver_path: Optional[str] = "./chromedriver.exe",
            screenshot_dir: Optional[str] = "logs/screenshots",
            headless: bool = False,
            disable_images: bool = True,
            user_data_dir: Optional[str] = None,
            extra_args: Optional[List[str]] = None
            ):
        self.driver_path = driver_path
        self.headless = headless
        self.disable_images = disable_images    
        self.user_data_dir = user_data_dir
        self.extra_args = extra_args

        self.browser: Optional[webdriver.Chrome] = None
        self.actions: Optional[ActionChains] = None
        self.tabs: dict[str, str] = {}  # danh sách tên tab {name: handle}
        self.downloaded: List[str] = []  # những file đã báo hoàn tất
        self.screenshot_dir = screenshot_dir
        
        if self.screenshot_dir and not os.path.exists(str(self.screenshot_dir)):
            os.makedirs(str(self.screenshot_dir))

    # ---------------------------------------------------------
    # 1. Lifecycle Management
    # ---------------------------------------------------------

    @retry(times=2, delay=1.0, exceptions=(WebDriverException,))
    def begin(self):
        """Khởi chạy trình duyệt và mở tab downloads làm mặc định."""
        if self.browser:
            logger.info("Đã tồn tại browser đang chạy -> bỏ qua khởi tạo.")
            return
        
        chrome_options = self._build_options()
        if self.user_data_dir:
            chrome_options.add_argument(f"--user-data-dir={self.user_data_dir}")

        self.driver_path = self._choose_driver_path() # Store resolved path
        service = Service(self.driver_path)
        self.browser = webdriver.Chrome(service=service, options=chrome_options)
        self.actions = ActionChains(self.browser)

        # Mở tab đầu tiên là trang downloads
        self.browser.get("chrome://downloads/")
        handle = self.browser.current_window_handle
        self.tabs["downloads"] = handle

    def close(self):
        """Đóng toàn bộ trình duyệt."""
        try:
            if self.browser:
                self.browser.quit()
                logger.info("Chrome đã đóng.")
        finally:
            self.browser = None
            self.actions = None
            self.tabs = {}

    # ---------------------------------------------------------
    # 2. Navigation & Tab Management
    # ---------------------------------------------------------

    def open_new_tab(self, url: str, name: Optional[str] = None) -> str:
        """Mở tab mới. Trả về tên tab (name hoặc handle)."""
        if not self.browser: return ""
        old_handles = set(self.browser.window_handles)
        self.browser.execute_script(f'window.open("{url}");')

        for _ in range(20):
            new_handles = set(self.browser.window_handles)
            diff = new_handles - old_handles
            if diff:
                handle = diff.pop()
                break
            time.sleep(0.1)
        else:
            raise RuntimeError("Không tìm thấy tab mới sau 2 giây.")

        final_name = name if name else handle
        self.tabs[final_name] = handle
        return final_name

    def switch_to_tab(self, name: str):
        """Chuyển focus sang tab theo tên."""
        if not self.browser: return
        if name not in self.tabs:
            raise ValueError(f"Không tìm thấy tab tên: {name}")
        self.browser.switch_to.window(self.tabs[name])

    def openUrl(self, url: str, name: Optional[str] = None):
        """Mở URL trên tab hiện tại."""
        if not self.browser: return
        self.browser.get(url)
        self.browser.refresh()
        if name:
            self.tabs[name] = self.browser.current_window_handle

    def current_tab(self) -> Optional[str]:
        """Lấy tên tab đang active."""
        if not self.browser: return None
        curr = self.browser.current_window_handle
        for name, handle in self.tabs.items():
            if handle == curr: return name
        return None

    def list_tabs(self) -> List[str]:
        """Danh sách tên các tab."""
        return list(self.tabs.keys())

    # ---------------------------------------------------------
    # 4. Wait Helpers
    # ---------------------------------------------------------

    def wait_xpath(self, xpath: str, timeout: int = 10) -> bool:
        return self._find_presence(xpath, timeout) is not None

    def wait_visible_xpath(self, xpath: str, timeout: int = 10) -> bool:
        return self._find_visible(xpath, timeout) is not None

    def get_xpath(self, xpath: str, timeout: float = 2.0) -> Optional[Any]:
        return self._find_presence(xpath, timeout)

    def get_all_xpath(self, xpath: str, timeout: float = 2.0) -> List[Any]:
        if not self.browser: return []
        try:
            return WebDriverWait(self.browser, timeout).until(
                EC.presence_of_all_elements_located((By.XPATH, xpath))
            )
        except TimeoutException:
            return []

    def check_xpath(self, xpath: str) -> bool:
        if not self.browser: return False
        return len(self.browser.find_elements(By.XPATH, xpath)) > 0

    def count_xpath(self, xpath: str) -> int:
        if not self.browser: return 0
        return len(self.browser.find_elements(By.XPATH, xpath))

    def is_visible(self, xpath: str) -> bool:
        if not self.browser: return False
        elements = self.browser.find_elements(By.XPATH, xpath)
        return elements[0].is_displayed() if elements else False

    def count_xpath(self, xpath: str) -> int:
        if not self.browser: return 0
        return len(self.browser.find_elements(By.XPATH, xpath))

    # ---------------------------------------------------------
    # 5. User Interaction
    # ---------------------------------------------------------

    def click_xpath(self, xpath: str, timeout: int = 10, scroll: bool = True):
        ele = self.get_xpath(xpath, timeout)
        if not ele:
            raise NoSuchElementException(f"Timeout {timeout}s finding: {xpath}")
        if scroll:
            self.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'})", ele)
        
        WebDriverWait(self.browser, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        ele.click()
        return True

    def click_force(self, xpath: str, timeout: int = 10) -> bool:
        ele = self.get_xpath(xpath, timeout)
        if not ele:
            self.capture_error("force_click_not_found")
            return False

        try:
            self.execute_script("arguments[0].scrollIntoView({block: 'center'});", ele)
            ele.click()
            return True
        except Exception:
            try:
                self.execute_script("arguments[0].click();", ele)
                logger.info(f"[Force Click] JS success: {xpath}")
                return True
            except Exception as e:
                logger.error(f"[Force Click Fail] {e}")
                self.capture_error("force_click_failed")
                return False

    def send_keys_xpath(self, xpath: str, text_or_keys: list | str, timeout: int = 10, clear: bool = True):
        ele = self.get_xpath(xpath, timeout)
        if not ele:
            raise NoSuchElementException(f"Cannot find: {xpath}")
        
        if clear: ele.clear()
        
        if isinstance(text_or_keys, str):
            ele.send_keys(text_or_keys)
        elif isinstance(text_or_keys, list):
            for item in text_or_keys:
                key = SPECIAL_KEYS.get(item.upper(), item)
                ele.send_keys(key)
        return True

    # ---------------------------------------------------------
    # 6. Extraction Helpers
    # ---------------------------------------------------------

    def get_text(self, xpath: str, timeout: int = 10) -> Optional[str]:
        ele = self.get_xpath(xpath, timeout)
        return ele.text if ele else None

    def get_attribute(self, xpath: str, attr: str, timeout: int = 10) -> Optional[str]:
        ele = self.get_xpath(xpath, timeout)
        return ele.get_attribute(attr) if ele else None

    # ---------------------------------------------------------
    # 7. Advanced Browser Control
    # ---------------------------------------------------------

    def execute_script(self, script: str, *args):
        if not self.browser: return None
        return self.browser.execute_script(script, *args)

    def move_to_element(self, xpath: str, timeout: int = 10):
        if not self.browser or not self.actions: return
        ele = self.get_xpath(xpath, timeout)
        if not ele:
            raise NoSuchElementException(f"Cannot hover: {xpath}")
        self.actions.move_to_element(ele).perform()

    def set_zoom(self, percent: int):
        self.execute_script(f"document.body.style.zoom='{percent}%'")

    def scroll_by(self, x: int = 0, y: int = 0):
        self.execute_script(f"window.scrollBy({x},{y})")

    def fetch_json_via_js(self, url: str, timeout: int = 10):
        js = f"return fetch('{url}').then(r=>r.json()).then(j=>JSON.stringify(j));"
        try:
            res = WebDriverWait(self.browser, timeout).until(lambda d: d.execute_script(js))
            return json.loads(res)
        except Exception as e:
            logger.warning(f"fetch_json error: {e}")
            return None

    # ---------------------------------------------------------
    # 8. Feature: Downloads
    # ---------------------------------------------------------

    def wait_for_download_complete(self, timeout: int = 60, poll: float = 1.0) -> Optional[str]:
        try:
            if 'downloads' not in self.tabs:
                self.browser.get('chrome://downloads/')
                self.tabs['downloads'] = self.browser.current_window_handle
            else:
                self.switch_to_tab('downloads')
        except: pass

        end = time.time() + timeout
        while time.time() < end:
            item = self._read_downloads_manager()
            if item and item.path and item.is_completed:
                path_str = str(item.path)
                if path_str and os.path.isfile(path_str):
                    if path_str not in self.downloaded:
                        self.downloaded.append(path_str)
                    return path_str
            time.sleep(poll)
        return None

    # ---------------------------------------------------------
    # 9. Debug & Utilities
    # ---------------------------------------------------------

    def capture_error(self, prefix: str = "error") -> Optional[str]:
        return self._save_screenshot(prefix)

    def screenshot(self, filename: str):
        """Chụp ảnh màn hình lưu vào logs/screenshots."""
        if not self.browser or not self.screenshot_dir: return
        fp = os.path.join(str(self.screenshot_dir), filename)
        self.browser.save_screenshot(fp)
        logger.info(f"Screenshot saved: {fp}")

    # ---------------------------------------------------------
    # 10. Internal Helpers
    # ---------------------------------------------------------

    def _check_version_compatibility(self, driver_path: str):
        """Kiểm tra tương thích giữa Chrome và Driver."""
        import subprocess
        try:
            # 1. Lấy version Chrome (Windows)
            if os.name == 'nt':
                cmd = 'powershell -command "(Get-Item \'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe\').VersionInfo.ProductVersion"'
                chrome_ver = subprocess.check_output(cmd, shell=True).decode().strip()
            else: # Linux
                chrome_ver = subprocess.check_output(['google-chrome', '--version']).decode().strip().split()[-1]
            
            # 2. Lấy version Driver
            driver_ver_raw = subprocess.check_output([driver_path, '--version']).decode().strip()
            driver_ver = driver_ver_raw.split()[1] # Ví dụ: "ChromeDriver 123.0.xxx" -> "123.0.xxx"
            
            major_chrome = chrome_ver.split('.')[0]
            major_driver = driver_ver.split('.')[0]
            
            if major_chrome != major_driver:
                logger.warning(f"[VERSION] Co the ton tai rui ro ko tuong thich: Chrome {major_chrome} vs Driver {major_driver}")
            else:
                logger.info(f"[VERSION] Chrome & Driver tuong thich (v{major_chrome})")
        except Exception as e:
            logger.info(f"[VERSION] Khong the kiem tra phien ban: {e}")

    def _choose_driver_path(self) -> str:
        cache_file = "logs/paths.json"
        if not os.path.exists("logs"): os.makedirs("logs")
        
        # 1. Luu tru duong dan hop le (Cache)
        cached_path = ""
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cached_path = json.load(f).get("chromedriver_path", "")
            except: pass

        # 2. Thu tu tim kiem
        candidates = [
            self.driver_path,        # Khoi tao ban dau
            "./chromedriver.exe",    # Mac dinh folder phan mem
            "./chromedriver",        # Linux mac dinh
            cached_path,             # Tu gia tri luu tru
            "/usr/bin/chromedriver"  # System path Linux
        ]
        
        # Loc bo trung lap và None
        candidates = list(dict.fromkeys([c for c in candidates if c]))
        
        for c in candidates:
            if os.path.exists(c):
                final_path = os.path.abspath(c)
                self._check_version_compatibility(final_path)
                # Luu lai neu tim thay path moi
                if final_path != cached_path:
                    try:
                        with open(cache_file, 'w') as f:
                            json.dump({"chromedriver_path": final_path}, f)
                    except: pass
                return final_path
        
        # 3. Last resort: Thu gui interface de nguoi dung cung cap path
        logger.info("[WARN] Khong tim thay Chromedriver. Vui long cung cap duong dan.")
        try:
            path = ""
            # Buoc 3a: Nhap thu cong duong dan (Toi uu neu da copy san path)
            try:
                import pymsgbox
                path = pymsgbox.prompt("Buoc 1/2: Nhap duong dan Chromedriver (Hoac nhan Cancel de chon tep):", 
                                       default="D:/Softwares/chromedriver.exe")
            except: pass
            
            # Buoc 3b: Chon tep qua cua so Explorer (Neu Buoc 3a bo qua)
            if not path or not os.path.exists(path):
                try:
                    from tkinter.filedialog import askopenfilename
                    import tkinter as tk
                    root = tk.Tk()
                    root.withdraw()
                    path = askopenfilename(title='Buoc 2/2: Chon tep chromedriver.exe', 
                                         filetypes=[("exe", "*.exe"), ("all", "*")])
                    root.destroy()
                except: pass
                
            if path and os.path.exists(path):
                # Luu lai path hop le duy nhat de lan sau khoi hoi
                with open(cache_file, 'w') as f:
                    json.dump({"chromedriver_path": path}, f)
                return path
        except Exception as e:
            logger.warning(f"[ERROR] Khong the thuc hien thu thap duong dan: {e}")
        
        raise FileNotFoundError(f"Khong tim thay Chromedriver. Vui long dat file vao folder phan mem hoac cau hinh dung.")

    def _build_options(self) -> Options:
        opts = Options()
        if self.headless:
            opts.add_argument("--headless=new")
            opts.add_argument("--disable-gpu")
            
        if self.extra_args:
            for arg in self.extra_args:
                opts.add_argument(arg)
        
        img_pref = 2 if self.disable_images else 1
        opts.add_experimental_option('prefs', {
            "profile.managed_default_content_settings.images": img_pref,
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': True,
        })
        opts.add_experimental_option("excludeSwitches", ["enable-automation"]) 
        opts.add_experimental_option('useAutomationExtension', False)
        return opts

    def _save_screenshot(self, prefix: str) -> Optional[str]:
        if not self.browser or not self.screenshot_dir:
            return None
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fp = os.path.join(str(self.screenshot_dir), f"{prefix}_{ts}.png")
            if self.browser:
                # Tạo thêm snapshot page source để debug sâu hơn nếu cần (Tuỳ chọn)
                # with open(f"logs/{prefix}_{ts}.html", "w", encoding="utf-8") as f:
                #     f.write(self.browser.page_source)
                self.browser.save_screenshot(fp)
                logger.info(f"Screenshot saved: {fp}")
                return fp
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
        return None

    def _find_presence(self, xpath: str, timeout: float) -> Optional[Any]:
        if not self.browser: return None
        try:
            return WebDriverWait(self.browser, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
        except: return None

    def _find_visible(self, xpath: str, timeout: float) -> Optional[Any]:
        if not self.browser: return None
        try:
            return WebDriverWait(self.browser, timeout).until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )
        except: return None

    def _read_downloads_manager(self) -> Optional[DownloadItem]:
        if not self.browser: return None
        js = '''
        try {
            const m = document.querySelector('downloads-manager');
            const i = m.shadowRoot.querySelectorAll('#downloadsList downloads-item')[0].shadowRoot;
            return JSON.stringify({
                title: i.querySelector('#name')?.textContent || '',
                description: i.querySelector('.description')?.textContent || '',
                path: i.querySelector('#file-icon')?.getAttribute('src') || ''
            });
        } catch(e) { return null; }
        '''
        try:
            if not self.browser: return None
            raw = self.browser.execute_script(js)
            if not raw: return None
            data = json.loads(raw)
            path = decode_chrome_file_icon_url(data.get('path', ''))
            return DownloadItem(title=data.get('title',''), tag='', description=data.get('description',''), path=path)
        except: return None
