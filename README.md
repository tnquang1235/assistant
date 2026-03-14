# 🤖 Assistant v1.3 - Trợ lý Cá Nhân
*(Cho những ai không đủ tiền để thuê một trợ lý chân dài)*

---

## 🚀 Tổng Quan Dự Án
**Assistant** là hệ thống trợ lý cá nhân tự động hóa, hoạt động 24/7 như một dịch vụ chạy ngầm. Hệ thống chuyên nghiệp hóa việc theo dõi thông tin, học tập và quản lý tài chính cá nhân thông qua tin nhắn Telegram, giúp triển khai trên đa nền tảng.

Hệ thống sử dụng triết lý **"Snapshot"**: Cung cấp thông tin cô đọng, nhanh gọn, tối ưu hoàn hảo cho trải nghiệm di động.

Dự án hiện nay đã được triển khai đến đến phiên bản 1.3

---

## 🌟 Tính Năng Cốt Lõi

### 🌦️ 1. Weather Snapshot
*   **Nguồn dữ liệu:** OpenWeatherMap API.
*   **Phạm vi:** Theo dõi cùng lúc nhiều địa điểm (Hồ Chí Minh, Cần Thơ, ...).
*   **Số liệu:** Nhiệt độ thực tế, Cảm giác như (Feels like), Độ ẩm, Tầm nhìn và Trạng thái thời tiết.

### 🧠 2. Smart English Learning (SRS)
*   **Thuật toán:** Spaced Repetition (SRS) dựa trên đường cong quên lãng Ebbinghaus.
*   **Lộ trình:** Tự động nhắc nhở ôn tập vào các mốc `+1`, `+3`, `+7`, `+30` ngày.
*   **B2 Grammar Challenge:** Tự động kích hoạt thử thách đặt câu với cấu trúc ngữ pháp cao cấp khi từ vựng thiếu ví dụ.
*   **Google Sheets:** Giúp người dùng có thể quản lý việc học của mình thủ công: thêm nghĩa từ, thay đổi ngày học, ngày ôn...

### 🌍 3. Global Finance Portal
*   **Nguồn:** Yahoo Finance (yfinance).
*   **Tài sản:** Chứng khoán Mỹ/Á/Âu, Vàng, Bạc, Bitcoin.
*   **Báo cáo:** So sánh biến động đa khung thời gian: 1 Ngày (1D), 1 Tuần (1W), 1 Tháng (1M), 1 Quý (1Q), 1 Năm (1Y).

### 🇻🇳 4. VN Stock Data Warehouse
*   **Công nghệ:** Scraper tùy chỉnh (Selenium/SCC) lấy dữ liệu trực tiếp từ bảng điện Vietstock.
*   **Data Warehouse:** Sử dụng Google Sheets làm kho lưu trữ lịch sử 27+ chỉ số kỹ thuật của nhóm VN30.
*   **Lọc thông minh:** 
    *   **Morning:** Cảnh báo mã cổ phiếu có sự kiện đặc biệt (`*`/`**`) & Giao dịch khối ngoại.
    *   **Mid-day/End-day:** Top mã kịch trần/sàn, Top biến động mạnh, Top thanh khoản đột biến.

---

## 🛠️ Yêu Cầu & Cấu Hình

| Thành phần | Yêu cầu kỹ thuật |
| :--- | :--- |
| **Ngôn ngữ** | Python 3.10+ (Thư viện: pandas, yfinance, selenium, gspread) |
| **Nền tảng** | Windows (Dev) / Raspberry Pi 4/5 (Server 24/7) |
| **Database** | Google Sheets API (Data Warehouse miễn phí) |
| **Trình duyệt** | Chrome (Windows) / Chromium (Linux) + Driver tương ứng |
| **Thông báo** | Telegram Bot API + Chat ID cá nhân |

---

## 📦 Cài Đặt Nhanh

**1. Clone dự án và cài thư viện:**
```bash
pip install -r requirements.txt
```

**2. Thiết lập "Bí mật quân sự":**
*   Đổi tên `samples/.env.example` -> `.env`.
*   Điền thông tin Token, API Keys và ID Sheets.
*   Đặt file chứng chỉ `service-account.json` vào thư mục gốc.

**3. Khởi chạy:**
```bash
python main.py
```
> *Assistant v1.3 sẽ tự động thức dậy vào các khung giờ: 06:00, 12:00, 16:00 và 22:00.*

---

## 🍓 Triển Khai Raspberry Pi (Server 24/7)

Hệ thống tự động phát hiện hệ điều hành (**Auto-Detect OS**) để cấu hình **Chrome Controller**:
*   **Auto-Linux Path:** Trỏ trực tiếp vào `/usr/bin/chromedriver`.
*   **Resource Optimization:** Tự động kích hoạt các cờ `--no-sandbox` và `--disable-dev-shm-usage` để chạy ổn định trên RAM hạn chế của Pi.

**Cài đặt trên Linux:**
```bash
sudo apt-get update && sudo apt-get install chromium-browser chromium-chromedriver
```

---

## 📁 Kiến Trúc Hệ Thống (Modular Design)
```text
assistant_v1.3/
├── main.py                # "Nhạc trưởng" điều phối lịch trình
├── config.py              # Bộ lọc biến môi trường và Validation
├── modules/               # Các cơ quan chức năng độc lập
│   ├── vn_finance.py      # VN30 Data Warehouse Scraper (Vietstock)
│   ├── finance.py         # World Market Analyzer (Yahoo Finance)
│   ├── english.py         # SRS Learning Engine (Ebbinghaus)
│   ├── weather.py         # Weather Snapshot (OpenWeatherMap)
│   ├── google_sheets.py   # Persistent Data Connection
│   └── notifier.py        # Telegram Push Gateway
├── scc/                   # Chrome Controller Core (v1.3 ARM Optimized)
├── samples/               # Bản vẽ kỹ thuật & Metadata Headers
└── .env                   # Tệp cấu hình bảo mật (Local only)
```

---

## 🚀 Lộ Trình Phát Triển (Roadmap)
- [ ] 📊 **Visual Analytics:** Chụp ảnh Heatmap & Chart gửi qua Telegram.
- [ ] 🤖 **Interactive Commands:** Ra lệnh cho Bot qua tin nhắn (Webhook mode).
- [ ] 📉 **Techanical Alerts:** Cảnh báo RSI/MACD tự động từ kho dữ liệu Google Sheets.

---
*Created with ❤️ for smarter management.*
