import os
import json
import time
import logging
import subprocess
import platform
import re
from datetime import datetime
from typing import Optional, List, Any

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, JavascriptException

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
            driver_path: Optional[str] = None,
            screenshot_dir: Optional[str] = None,
            headless: bool = False,
            disable_images: bool = True,
            user_data_dir: Optional[str] = None,
            capture_on_error: bool = True,
            extra_args: Optional[List[str]] = None
            ):
        self.driver_path = driver_path
        self.headless = headless
        self.disable_images = disable_images    
        self.user_data_dir = user_data_dir
        self.capture_on_error = capture_on_error
        self.extra_args = extra_args

        # Đường dẫn dự án (parent của scc)
        self.project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Cấu hình screenshot: ưu tiên user truyền vào, sau đó đến mặc định
        if not screenshot_dir:
            self.screenshot_dir = os.path.join(self.project_dir, "logs/screenshots")
        else:
            self.screenshot_dir = screenshot_dir

        self.browser: Optional[webdriver.Chrome] = None
        self.actions: Optional[ActionChains] = None
        self.tabs: dict[str, str] = {}
        self.downloaded: List[str] = []

        if not os.path.exists(str(self.screenshot_dir)):
            try:
                os.makedirs(str(self.screenshot_dir))
            except: pass

        self.config_path = os.path.join(self.project_dir, "scc_config.json")

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

        d_path = self._choose_driver_path()
        self.check_version_compatibility(d_path)
        
        service = Service(d_path)
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

    # ---------------------------------------------------------
    # 4. Elements & Waiting (Consolidated)
    # ---------------------------------------------------------

    def find_element(self, xpath: str, timeout: float = 10, visible: bool = False) -> Optional[Any]:
        """Hàm chính để tìm phần tử (chờ đến khi hiện diện hoặc hiển thị)."""
        if not self.browser: return None
        try:
            condition = EC.visibility_of_element_located if visible else EC.presence_of_element_located
            return WebDriverWait(self.browser, timeout).until(condition((By.XPATH, xpath)))
        except TimeoutException:
            return None
        except Exception as e:
            logger.error(f"Lỗi find_element ({xpath}): {e}")
            return None

    def find_elements(self, xpath: str, timeout: float = 10) -> List[Any]:
        """Tìm danh sách phần tử."""
        if not self.browser: return []
        try:
            return WebDriverWait(self.browser, timeout).until(
                EC.presence_of_all_elements_located((By.XPATH, xpath))
            )
        except:
            return []

    def wait_xpath(self, xpath: str, timeout: int = 10) -> bool:
        """Đợi xpath hiện diện."""
        return self.find_element(xpath, timeout) is not None

    def wait_visible_xpath(self, xpath: str, timeout: int = 10) -> bool:
        """Đợi xpath hiển thị."""
        return self.find_element(xpath, timeout, visible=True) is not None

    def get_xpath(self, xpath: str, timeout: float = 10) -> Optional[Any]:
        """Lấy element theo xpath."""
        return self.find_element(xpath, timeout)

    def check_xpath(self, xpath: str) -> bool:
        """Kiểm tra nhanh xpath có tồn tại không (không chờ)."""
        if not self.browser: return False
        return len(self.browser.find_elements(By.XPATH, xpath)) > 0

    def is_visible(self, xpath: str) -> bool:
        """Kiểm tra xpath có đang hiển thị không (không chờ)."""
        if not self.browser: return False
        elements = self.browser.find_elements(By.XPATH, xpath)
        return elements[0].is_displayed() if elements else False

    def count_xpath(self, xpath: str) -> int:
        """Đếm số lượng phần tử khớp xpath."""
        if not self.browser: return 0
        return len(self.browser.find_elements(By.XPATH, xpath))

    # ---------------------------------------------------------
    # 5. User Interaction
    # ---------------------------------------------------------

    def click_xpath(self, xpath: str, timeout: int = 10, scroll: bool = True):
        """Click vào phần tử sau khi đợi nó có thể click."""
        try:
            ele = self.find_element(xpath, timeout, visible=True)
            if not ele:
                raise NoSuchElementException(f"Timeout {timeout}s finding: {xpath}")
            
            if scroll:
                self.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'})", ele)
            
            WebDriverWait(self.browser, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            ele.click()
            return True
        except Exception as e:
            if self.capture_on_error:
                self.capture_error(f"click_fail_{int(time.time())}")
            logger.error(f"Lỗi click_xpath: {e}")
            raise

    def click_force(self, xpath: str, timeout: int = 10) -> bool:
        """Click cưỡng bức bằng JS nếu click thường thất bại."""
        ele = self.find_element(xpath, timeout)
        if not ele:
            if self.capture_on_error:
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
                if self.capture_on_error:
                    self.capture_error("force_click_failed")
                return False

    def send_keys_xpath(self, xpath: str, text_or_keys: list | str, timeout: int = 10, clear: bool = True):
        """Gửi phím/chuỗi đến phần tử."""
        try:
            ele = self.find_element(xpath, timeout, visible=True)
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
        except Exception as e:
            if self.capture_on_error:
                self.capture_error(f"send_keys_fail_{int(time.time())}")
            logger.error(f"Lỗi send_keys_xpath: {e}")
            raise

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

    def screenshot(self, filename: str) -> Optional[str]:
        """Chụp ảnh màn hình lưu vào screenshot_dir."""
        if not self.browser or not self.screenshot_dir: return None
        fp = os.path.join(str(self.screenshot_dir), filename)
        try:
            self.browser.save_screenshot(fp)
            logger.info(f"Screenshot saved: {fp}")
            return fp
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return None

    # ---------------------------------------------------------
    # 10. Driver Version & Compatibility
    # ---------------------------------------------------------

    def get_chrome_version(self) -> Optional[str]:
        """Lấy phiên bản Chrome từ registry (Windows) hoặc command (Linux/Rasp).</str>"""
        if platform.system() == 'Windows':
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                v, _ = winreg.QueryValueEx(key, "version")
                return str(v)
            except:
                return None
        else:
            try:
                # Thử Chromium (Raspberry) trước rồi tới Chrome
                try:
                    res = subprocess.check_output(['chromium-browser', '--version'], text=True)
                except:
                    res = subprocess.check_output(['google-chrome', '--version'], text=True)
                match = re.search(r'[\d.]+', res)
                return match.group(0) if match else None
            except:
                return None

    def get_chromedriver_version(self, path: str) -> Optional[str]:
        """Lấy phiên bản ChromeDriver từ file thực thi."""
        try:
            res = subprocess.check_output([path, '--version'], text=True)
            match = re.search(r'chromedriver\s+([\d.]+)', res, re.I)
            return match.group(1) if match else None
        except:
            return None

    def check_version_compatibility(self, driver_path: str):
        """So sánh phiên bản Chrome hiện tại với ChromeDriver."""
        chrome_v = self.get_chrome_version()
        driver_v = self.get_chromedriver_version(driver_path)
        if not chrome_v or not driver_v:
            logger.warning(f"Không thể xác định phiên bản để so sánh: Chrome={chrome_v}, Driver={driver_v}")
            return
        
        c_major = chrome_v.split('.')[0]
        d_major = driver_v.split('.')[0]
        if c_major != d_major:
            logger.warning(f"LƯU Ý: Chrome v{chrome_v} và ChromeDriver v{driver_v} có version chính khác nhau ({c_major} vs {d_major}).")
        else:
            logger.info(f"Version tương thích: Chrome v{chrome_v}, ChromeDriver v{driver_v}")

    # ---------------------------------------------------------
    # 11. Internal Helpers
    # ---------------------------------------------------------

    def _choose_driver_path(self) -> str:
        """Tìm ChromeDriver linh hoạt theo ưu tiên."""
        # 1. User cung cấp khi khởi tạo
        if self.driver_path and os.path.exists(self.driver_path):
            self._save_config(self.driver_path)
            return str(self.driver_path)

        # 2. File cùng thư mục dự án
        for name in ["chromedriver.exe", "chromedriver"]:
            project_path = os.path.join(self.project_dir, name)
            if os.path.exists(project_path):
                self._save_config(project_path)
                return project_path

        # 2.5 Hỗ trợ Linux / Raspberry Pi OS path mặc định
        if platform.system() != 'Windows':
            for l_path in ["/usr/bin/chromedriver", "/usr/lib/chromium-browser/chromedriver", "/usr/local/bin/chromedriver"]:
                if os.path.exists(l_path):
                    self._save_config(l_path)
                    return l_path

        # 3. Đường dẫn đã dùng lần trước (lưu trong config)
        last_path = self._get_last_driver_path()
        if last_path and os.path.exists(last_path):
            logger.info(f"Sử dụng ChromeDriver từ lần trước: {last_path}")
            return last_path

        # 4. Hỏi người dùng qua GUI (Lazy import, bọc lỗi cho môi trường Headless/Linux)
        try:
            import pymsgbox
            import tkinter as tk
            from tkinter.filedialog import askopenfilename
            
            logger.info("Yêu cầu chọn chromedriver qua dialog...")
            pbox_path = pymsgbox.prompt("Nhập đường dẫn chromedriver (hoặc nhấp Cancel để chọn file):")
            if pbox_path and os.path.exists(pbox_path):
                self._save_config(pbox_path)
                return pbox_path
            
            root = tk.Tk()
            root.withdraw()
            selected = askopenfilename(title='Select Chrome Driver', filetypes=[("exe", "*.exe"), ("all", "*")])
            root.destroy()
            
            if selected and os.path.exists(selected):
                self._save_config(selected)
                return selected
        except ImportError:
            logger.warning("Không thể load thư viện GUI (pymsgbox, tkinter) - Bỏ qua bước chọn dialog.")
        except Exception as e:
            logger.warning(f"Lỗi khi hiển thị dialog chọn file (có thể do thiếu môi trường Window/Display): {e}")
        
        raise FileNotFoundError("Không tìm thấy Chromedriver theo cấu hình, vui lòng cài đặt hoặc truyền đường dẫn cụ thể vào driver_path.")

    def _save_config(self, driver_path: str):
        try:
            data = {"last_driver_path": driver_path}
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except: pass

    def _get_last_driver_path(self) -> Optional[str]:
        if not os.path.exists(self.config_path):
            return None
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("last_driver_path")
        except:
            return None

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
                self.browser.save_screenshot(fp)
                logger.info(f"Screenshot saved: {fp}")
                return fp
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return None

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
