import logging
import time
import urllib.parse
from typing import Optional, Callable

# -----------------------------
# Cấu hình logger
# -----------------------------
logger = logging.getLogger("ChromeController")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)

# -----------------------------
# Retry decorator
# -----------------------------

def retry(times: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)) -> Callable:
    """Decorator để thử lại khi hàm ném exception.
    times: số lần thử (không tính lần đầu) -> tổng số lần chạy = times
    delay: giây giữa các lần thử
    exceptions: tuple các exception cần catch
    """
    def _decorator(func: Callable) -> Callable:
        def _wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    logger.warning(f"{func.__name__} thất bại (lần {attempt}/{times}), sẽ thử lại sau {delay}s: {e}")
                    time.sleep(delay)
            # Thử lần cuối ra lỗi
            logger.error(f"{func.__name__} thất bại sau {times} lần: {last_exc}")
            raise last_exc
        return _wrapper
    return _decorator

# -----------------------------
# Helper: decode chrome file icon url
# -----------------------------

def decode_chrome_file_icon_url(url: str) -> Optional[str]:
    """
    Giải mã URL chrome file icon lấy tham số path.
    Ví dụ: "filesystem:C:\\..." được decode về đường dẫn file thật.
    Trả về None nếu không parse được.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        encoded_path = params.get("path", [None])[0]
        if encoded_path:
            return urllib.parse.unquote(encoded_path)
        # Đôi khi path nằm trực tiếp ở phần path của url
        if parsed.path:
            return urllib.parse.unquote(parsed.path)
    except Exception as e:
        logger.debug(f"decode_chrome_file_icon_url lỗi: {e}")
    return None
