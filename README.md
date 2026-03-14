# 🤖 Assistant v1.3 - Tự Động Hóa Quản Lý Cá Nhân

Assistant v1.3 là một hệ thống trợ lý cá nhân đa năng, hoạt động như một dịch vụ chạy ngầm trên máy tính nhằm tự động thu thập dữ liệu và gửi các bản tin tóm tắt hàng ngày qua thư viện Telegram Bot. Dự án sử dụng mô hình kiến trúc dạng Modular (các file module độc lập được lập lịch từ `main.py`) giúp tối ưu quá trình bảo trì và phát triển.

Dự án hiện đang hỗ trợ 4 tính năng chính: **Thông tin Thời tiết, Học và Ôn Tiếng Anh, Chứng Khoán Thế Giới** và **Chứng Khoán Việt Nam**.

Lưu ý: Bạn không cần sở hữu cơ sở dữ liệu riêng, hệ thống lấy **Google Sheets** làm điểm kết nối Cloud trung tâm - biến nó thành "Data Warehouse" cá nhân hoàn toàn miễn phí.

---

## 🌟 Chức Năng Nổi Bật 🌟

### 1. 🌦 Thông Tin Thời Tiết (Weather Module)
- Tích hợp **OpenWeatherMap API**.
- Báo cáo thời tiết nhanh dạng "Snapshot" qua Telegram (hiển thị tốt trên mobile).
- Theo dõi nhiều thành phố cùng lúc (VD: Hồ Chí Minh, Cần Thơ) với các chỉ số: Nhiệt độ, Cao/Thấp, Độ ẩm và Trạng thái.

### 2. 🧠 Học Tiếng Anh cùng Spaced Repetition (English Module)
Thuật toán được thiết kế dựa trên lý thuyết "Đường cong quên lãng" (Ebbinghaus). Giúp học ít mà nhớ bền bằng cách ôn tập ngắt quãng:
- **Nguyên lý SRS**: Tự động tính toán hiển thị lại các từ vựng vào ngày `+1`, `+3`, `+7`, `+30` và random `60-90` ngày.
- **Tính năng Challenge**: Từ nào chưa có ví dụ (Example), Bot sẽ yêu cầu (trigger) cấu trúc B2 ngẫu nhiên để bạn nghĩ ra ví dụ tương thích.
- Bảng từ vựng lấy trực tiếp từ Google Sheets, chia ca linh hoạt linh động cho sáng/trưa/chiều.

### 3. 🌍 Thị Trường Thế Giới (Finance Module)
- Tích hợp **Yahoo Finance API (yfinance)** để gọi số liệu đa quốc gia.
- Theo dõi đủ các loại tài sản: Chỉ số chứng khoán (SP500, DowJones, Nikkei...), Hàng hoá (Gold, Silver), Tiền điện tử (Bitcoin)...
- **Theo dõi biến động sâu sắc**: Tính và xuất thẳng báo cáo 1 Ngày (1D), 1 Tuần (1W), 1 Tháng (1M), 1 Quý (1Q) và 1 Năm (1Y) cho đa tài sản trên một màn hình Telegram gọn gàng, ngay ngắn.

### 4. 🇻🇳 Chứng Khoán Việt Nam (VNFinance Module) - *Data Warehouse Tự Động*
- Không phụ thuộc API bên thứ 3 mắc mỏ hoặc trễ nhịp. Sử dụng **Selenium/SCC** để lấy giá trực tiếp từ bảng điện Vietstock (VN30).
- **Google Sheets Data Warehouse**: Toàn bộ hơn 27 chỉ số kĩ thuật (Giá trần/sàn, Bid/Ask Price, Volume, Ngoại khối...) sẽ được tự động cào (scrape) và "đắp" liên tục vào Sheet. Tự động sinh thêm tên Cột nếu bạn tùy biến mã nguồn thêm trường mới. Dữ liệu chốt cuối ngày sẽ nằm lại vĩnh viễn trên sheet tạo thành kho Database riêng cho sau này.
- **Bản tin Telegram Lọc Thông Minh (No Repetition)**:
  - *Sáng (Morning)*: Nhắc cổ tức/sự kiện (`*` / `**`) và dòng tiền Khối ngoại hôm qua.
  - *Trưa/Chiều (Noon/Afternoon)*: Quét 3 mã kịch biên độ (Sàn/Trần), 3 mã Biến động mạnh nhất, 3 mã Thanh Khoản Đột biến và Báo cáo riêng biệt Khối lượng Mua Ròng/Bán Ròng Khối Ngoại.

---

## 🛠 Hướng Dẫn Cài Đặt và Khởi Chạy

### Cài đặt môi trường
Đảm bảo bạn đã cài Python (>=3.10) và pip:
```bash
pip install -r requirements.txt
```

### Chuẩn bị kết nối
1. Copy file `.env.example` thành file có tên `.env` ở thư mục gốc. Điền đầy đủ:
   - Token & Chat ID Telegram.
   - API Key của OpenWeatherMap.
   - Các ID Google Sheet của bạn.
2. Tải File Credentials dạng JSON của **Google Cloud Service Account**, đổi tên hoặc cấu hình đúng đường dẫn nằm trong `.env`. Share quyền "Editor" của từng Sheet qua email của Service Account này.
3. Download sẵn **ChromeDriver** cài vào thư mục chính để tool cào dữ liệu được cấp quyền.

### Khởi động Bot
Mở Cmd (Terminal) tại thư mục chứa dự án và gõ:
```bash
python main.py
```
> "Assistant v1.3 đang chạy..."
*Bot sẽ tự động ngủ (Sleep) và kích hoạt gửi bản tin chính xác theo lịch của máy ở các mốc: 06:00, 12:00, 16:00, 22:00.*

---

## 🍓 Triển Khai Server 24/7 (Linux & Raspberry Pi)

Assistant v1.3 được thiết kế tự động tương thích ngược giữa Windows (PC) và Linux (Raspberry Pi/Ubuntu) mà bạn **KHÔNG CẦN SỬA MÃ NGUỒN**.

Trọng tâm là thư viện cào số liệu **scc**, trên Windows hệ thống sử dụng file `chromedriver.exe` thông thường. Tuy nhiên, khi đưa lên các thiết bị chip ARM (Raspberry Pi), hệ thống sẽ tự động quét và áp dụng chế độ tối ưu tài nguyên:
- **Tự động nhận diện Linux:** Chuyển đường dẫn gọi Driver sang `/usr/bin/chromedriver`.
- **Tự động thêm cờ tối ưu (Flags):** Tự động đính kèm `--no-sandbox` (Bypass lỗi phân quyền root) và đặc biệt là `--disable-dev-shm-usage` (ép lưu tạm trên thẻ nhớ thay cho RAM - chống crash Memory-Leak khi tải trang Vietstock nặng trên máy ảo/Pi).

### Cách cài đặt trên Raspberry Pi (Debian/Ubuntu)
Thay vì tải thủ công file `.exe`, bạn chỉ cần chạy lệnh sau trên Terminal để hệ điều hành tải về bộ mã nguồn duyệt web cho kiến trúc ARM tương ứng:
```bash
sudo apt-get update
sudo apt-get install chromium-browser chromium-chromedriver
```
Sau đó, tiếp tục cài đặt `pip install -r requirements.txt` và chạy file `main.py` bình thường. Bot sẽ chạy siêu nhẹ và ổn định trong hàng tháng ròng rã!

---

## 📁 Cấu trúc thư mục (Modular Design)
```text
assistant_v1.3/
├── main.py                # Điểm khởi chạy chính & Scheduler
├── config.py              # Xử lý load System Environment (.env)
├── modules/               # Nơi chứa các tính năng độc lập
│   ├── english.py         # SRS Tiếng Anh
│   ├── finance.py         # World Finance Info
│   ├── vn_finance.py      # SCC Scrape data VN30 => Data Warehouse
│   ├── weather.py         # REST API Weather
│   ├── google_sheets.py   # Connection Manager, Dynamic Field Mapping
│   └── notifier.py        # Telegram Push Message
├── scc/                   # Thư viện Chrome Controller ẩn của user
├── samples/               # Định dạng mẫu (Headers) cho Google Sheets gốc
└── .env                   # Environment & Keys (Cần cung cấp ở Local)
```

## 📈 Lộ trình phát triển (Roadmap)
- [] Tích hợp Chart/Heatmap chụp ảnh màn hình gửi qua Telegram thay vì text chay.
- [] Xây dựng Logic Backtest cho dữ liệu trong Google Sheet Data Warehouse (Phân kì RSI/MACD,...).
- [] Khả năng ra lệnh Text Input thẳng trên nền Telegram cho Bot lập lịch/thêm từ vựng (Webhook mode).
