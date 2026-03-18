# 🚀 Selenium Chrome Controller (SCC)

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Selenium](https://img.shields.io/badge/selenium-4.x-green.svg)](https://www.selenium.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **SCC** là một lớp điều khiển (abstraction layer) tối ưu hóa Selenium, tập trung vào tính đơn giản, độ ổn định, và khả năng mở rộng trong các dự án tự động hóa trình duyệt.

**Phiên bản:** `2.1.1` | **Cập nhật:** `2026-03-18` | **Trạng thái:** Active

---

## 📋 Mục lục
- [🤖 Tác giả: Con người & AI (Gemini & ChatGPT)](#-tác-giả-con-người--ai-gemini--chatgpt)
- [⚖️ Tại sao nên dùng SCC?](#️-tại-sao-nên-dùng-scc-thay-vì-selenium-thuần)
- [📦 Cài đặt & Thư viện](#-cài-đặt--thư-viện)
- [🗂 Cấu trúc thư viện](#-cấu-trúc-thư-viện)
- [🔥 Tính năng nổi bật](#-tính-năng-nổi-bật)
- [💻 Ví dụ sử dụng nhanh](#-ví-dụ-sử-dụng-nhanh)
- [🎯 Cấu trúc lớp (Class Architecture)](#-cấu-trúc-lớp-class-architecture)
- [🛡 Chiến lược xử lý lỗi](#-chiến-lược-xử-lý-lỗi)
- [🛠 Xử lý sự cố](#-xử-lý-sự-cố-troubleshooting)
- [🤝 Đóng góp](#-đóng-góp-contributing)
- [📜 Giấy phép](#-giấy-phép-license)
- [🚀 Nhật ký Nâng cấp (Changelog)](#-nhật-ký-nâng-cấp-changelog)

---

## 🤖 Tác giả: Con người & AI (Gemini & ChatGPT)

Dự án được xây dựng dựa trên sự phối hợp rõ ràng về vai trò để tối ưu hiệu suất và đảm bảo khả năng bảo trì lâu dài:

*   **Con người (Tác giả)**: Định hướng phát triển, thiết lập luồng nghiệp vụ (business logic), đưa ra các yêu cầu kỹ thuật đặc thù và kiểm duyệt/ra quyết định cuối cùng cho mọi thay đổi.
*   **AI (Gemini & ChatGPT)**: Thực thi chi tiết mã nguồn, đảm bảo tiêu chuẩn cấu trúc (PEP8), tối ưu hóa các hàm bổ trợ, xử lý các trường hợp biên (edge cases) và soạn thảo hệ thống tài liệu.

> [!NOTE]
> Việc xác định rõ vai trò giúp việc đánh giá vấn đề và định hướng nâng cấp trong tương lai trở nên chính xác hơn. Tác giả sử dụng phương pháp **kiểm tra chéo (cross-checking)** giữa các công cụ AI để khai thác tối đa ưu điểm của từng model.

---

## ⚖️ Tại sao nên dùng SCC thay vì Selenium thuần?

| Tính năng | Selenium thuần | SCC |
|------------|----------------|------|
| Độ trễ website | ❌ Tự xử lý | ✅ Tích hợp wait, retry |
| Tự cuộn chuột | ❌ Dễ lỗi | ✅ Tự động trước khi diễn ra |
| Click Force | ❌ Click thường | ✅ Fallback sang JS (Click force) |
| Quản lý tab | ❌ Dùng `handle` phức tạp | ✅ Quản lý bằng `name` |
| Theo dõi tải file | ❌ Khó triển khai | ✅ Shadow DOM (Đã tích hợp) |
| Debug | ❌ Khó truy vết | ✅ Chụp ảnh tự động khi lỗi |

---

## 📦 Cài đặt & Thư viện

### Cách 1 – Sử dụng requirements.txt

```bash
pip install -r requirements.txt
```

### Cách 2 – Cài đặt thủ công

```bash
pip install selenium webdriver-manager pymsgbox retry python-dotenv pyyaml yfinance requests schedule pytz gspread oauth2client psycopg2-binary pandas
```

---

## 🗂 Cấu trúc thư viện

Thư viện được tổ chức theo module chuyên nghiệp để dễ dàng bảo trì và mở rộng:

```
scc/                    # Thư mục gói (Package)
├── __init__.py         # Export các thành phần chính (SCC class)
├── controller.py       # Lớp ChromeController chính (Trái tim của thư viện)
├── helpers.py          # Các công cụ hỗ trợ (logging, retry deco, url decoding...)
├── models.py           # Định nghĩa các cấu trúc dữ liệu (DownloadItem, v.v.)
└── constants.py        # Lưu trữ VERSION, phím tắt, cấu hình mặc định
```

---

## 🔥 Tính năng nổi bật

*   **⚡ Smart Action Engine**: Tự động cuộn chuột và chờ đợi phần tử hiển thị trước khi tương tác.
*   **🛡️ Click-Force**: Tự động fallback sang JavaScript click khi Selenium click không thực thi được.
*   **📑 Tab Management**: Hỗ trợ quản lý nhiều tab bằng `name`.
*   **📥 Downloads tracking**: Tự động theo dõi tiến trình tải file qua `chrome://downloads`.
*   **📸 Error & Screenshot Capture**: Chụp ảnh màn hình tự động vào thư mục `/logs` khi gặp lỗi. Đặc biệt, phương thức `capture_error()` giờ đây trả về đường dẫn file (`str`) để dễ dàng tích hợp với các hệ thống thông báo (như Telegram/Email).
*   **🧩 Anti-Detection**: Tích hợp cấu hình giả lập người dùng, bypass các hệ thống phát hiện bot cơ bản.

---

## 💻 Ví dụ sử dụng nhanh

```python
import scc

# Khởi tạo với cấu hình tối ưu
ctrl = scc.SCC(headless=False, disable_images=True)
ctrl.begin()

# Mở tab với nickname chuyên nghiệp
ctrl.open_new_tab("https://finance.vietstock.vn", name="vietstock")

# Tương tác mượt mà
if ctrl.wait_visible_xpath("//input[@id='txtSearch']"):
    ctrl.send_keys_xpath("//input[@id='txtSearch']", ["VN30", "ENTER"])

# Chờ và lấy file vừa tải về tự động
filepath = ctrl.wait_for_download_complete(timeout=30)
if filepath:
    print(f"✅ Data ready at: {filepath}")

ctrl.close()
```

---

## 🎯 Cấu trúc lớp (Class Architecture)

1. **Lifecycle**: `begin()`, `close()`.
2. **Navigation**: `open_new_tab()`, `switch_to_tab()`, `openUrl()`.
3. **Wait Helpers**: `wait_xpath()`, `wait_visible_xpath()` (trả về bool).
4. **Discovery**: `get_xpath()`, `get_all_xpath()`, `check_xpath()`, `count_xpath()`, `is_visible()`.
5. **Actions**: `click_xpath()`, `click_force()`, `send_keys_xpath()`.
6. **Advanced**: `execute_script()`, `set_zoom()`, `fetch_json_via_js()`.

---

## 🛡 Chiến lược xử lý lỗi

SCC áp dụng mô hình xử lý lỗi có cấu trúc giúp hệ thống automation ổn định:
*   **Timeout rõ ràng**: Mỗi thao tác chờ đều có giới hạn thời gian tránh treo script.
*   **Fallback có kiểm soát**: Chuyển sang phương thức thay thế (như JS) khi phương thức chuẩn lỗi.
*   **Logging & Screenshots**: Lưu nhật ký và hình ảnh vết lỗi tự động.
*   **Kiểu trả về nhất quán**: Sử dụng `bool` cho các hàm kiểm tra và `None` hoặc raise Exception cho các hàm hành động.

---

## 🛠 Xử lý sự cố (Troubleshooting)

1.  **Lỗi Chromedriver version mismatch**: 
    *   SCC sử dụng `webdriver-manager` để tự động tải driver. Nếu gặp lỗi, hãy thử xóa thư mục cache của driver trong user profile.
2.  **Không tìm thấy phần tử (Timeout)**: 
    *   Kiểm tra xem trang web có sử dụng Iframe hoặc Shadow DOM hay không.
    *   Tăng `timeout` trong các hàm `wait_*`, `get_*`.
3.  **Lỗi khi chạy ở chế độ Headless**: 
    *   Một số website chặn chế độ headless mặc định. Thử sử dụng các option giả lập `user-agent` trong `SCC` init.

---

## 🤝 Đóng góp (Contributing)

Mọi đóng góp nhằm cải thiện SCC đều được chào đón:
1. Fork dự án.
2. Tạo nhánh tính năng mới (`git checkout -b feature/AmazingFeature`).
3. Commit thay đổi (`git commit -m 'Add some AmazingFeature'`).
4. Push lên nhánh (`git push origin feature/AmazingFeature`).
5. Mở một Pull Request.

---

## 📜 Giấy phép (License)

Phân phối dưới Giấy phép MIT. Xem `LICENSE` để biết thêm thông tin.

---
 
## 🚀 Nhật ký Nâng cấp (Changelog)
 
### v2.1.1 (2026-03-18)
- **Feature (Critical)**: Nâng cấp phương thức `capture_error`. Hàm này hiện trả về đường dẫn file (`str`) của ảnh chụp màn hình thay vì chỉ thực thi ngầm. Việc này hỗ trợ tích hợp gửi ảnh báo lỗi trực quan qua các kênh thông báo ngoại vi (Telegram, Slack, Email).
- **Maintenance**: Cập nhật cơ chế lưu trữ tập trung vào thư mục `logs/screenshots`.
 
### v2.1.0 (2026-03-03)
- **Feature**: Tách biệt hoàn toàn `ChromeController` sang module độc lập.
- **Improvement**: Hỗ trợ headless mode tối ưu cho Linux/Docker.
 
---
*Phát triển bởi 🌱 **Quang Amateur** ✨, hỗ trợ bởi trợ lý AI 🤖. Hướng tới sự chuyên nghiệp và tin cậy.*
