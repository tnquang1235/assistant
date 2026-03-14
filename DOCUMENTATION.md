# 🤖 Assistant v1.2 - Comprehensive Documentation

Assistant v1.2 là hệ thống trợ lý cá nhân tự động gửi bản tin hàng ngày qua Telegram. Hệ thống tích hợp dữ liệu từ nhiều nguồn (OpenWeatherMap, Yahoo Finance) và quản lý tiến trình học tập tiếng Anh thông qua Google Sheets.

---

## 1. Cấu trúc bản tin (Thứ tự gửi mỗi lần)
Bản tin Assistant v1.2 được thiết kế theo triết lý **"Snapshot"**: hiển thị thông tin nhanh, gọn, chuyên nghiệp và tối ưu cho nhiều nền tảng, đặc biệt là Mobile (Telegram).

1.  **Lời chào & Thông tin thời tiết**: Lời chào và thông tin thời tiết 2 Thành phố là Cần Thơ và Hồ Chí Minh, Thông tin thời tiết Hiển thị dạng bảng (Thành phố, Nhiệt độ hiện tại, Cao/Thấp, Độ ẩm, Trạng thái).
2.  **Từ vựng Tiếng Anh**:
    *   **Từ mới**: Bao gồm Word, Type, IPA, Meaning và Example. 
    *   **Thử thách (Challenge)**: Nếu từ chưa có ví dụ, hệ thống sẽ gọi ý thử thách người dùng đặt câu với cấu trúc ngữ pháp cấp độ **B2** ngẫu nhiên.
    *   **Ôn tập**: Chỉ hiển thị Word và Type để ôn tập theo ngày, dựa theo thuật toán SRS.
3.  **Thị trường thế giới**: Gồm các nội dung: Chỉ số hiện tại, % thay đổi so với: 1D, 1W, 1M, 1Q, 1Y.
    *   **Cơ chế so sánh**: Sử dụng ngày dữ liệu mới nhất làm gốc. So sánh 1D dựa trên phiên liền kề gần nhất. Các mốc 1W, 1M, 1Q, 1Y được tính theo đúng ngày dương lịch (nếu trùng ngày nghỉ sẽ lùi về ngày giao dịch gần nhất trước đó).
    *   **Bản tin Sáng**: Toàn bộ chỉ số, sắp xếp theo độ **Mạnh-Yếu** (Biến động % 1D giảm dần).
    *   **Bản tin Trưa/Chiều/Tối**: Top 3 tăng mạnh nhất và Top 3 giảm mạnh nhất (theo 1D).
    *   **💡 Hướng dẫn định dạng Bảng (F-String Formatting)**: 
        *   **Độ nhạy (Precision)**: 
            *   Cột **1D**: Lấy **2 số thập phân** (`.2f`) để theo dõi sát biến động (độ nhạy cao) hàng ngày.
            *   Các cột **1W, 1M, 1Q, 1Y**: Lấy **số nguyên** (`.0f`) để tối ưu không gian và xem nhanh xu hướng.
        *   **Cấu trúc kỹ thuật**: Sử dụng f-string `{giá_trị : [căn_lề][dấu][độ_rộng].[thập_phân][kiểu]}`. Ví dụ: `{:>+7.2f}%` cho cột 1D.
4.  **Chứng khoán Việt Nam (VN30 & Data Warehouse)**: 
    *   **Kho dữ liệu (Google Sheets Data Warehouse)**: Do đặc thù dữ liệu chứng khoán Việt Nam khó lấy được lịch sử quá khứ chính xác qua API miễn phí, nên cần một "Kho dữ liệu" (Data warehouse) riêng biệt, và Google Sheets được sử dụng để lưu trữ dữ liệu. Dữ liệu được cào xước từ Vietstock trực tiếp trên bảng giá, sau đó sẽ được liên tục cập nhật/ghi đè đắp dần vào Google Sheets. Tính chất tự động mở rộng cột của phần mềm này cho phép theo dõi tới hơn 27 chỉ số (Giá Trực Tiếp, Volume, Khối ngoại mua/bán, v.v.). Cuối ngày (Afternoon), phiên bản ghi này sẽ chốt thành dữ liệu chính thức của ngày hôm đó (các khung giờ buổi tối sẽ không thực hiện chạy lại dữ liệu).
    *   **Bản tin Sáng (Morning)**: Tập trung vào "chuẩn bị phiên mới". Hiển thị các sự kiện (Cổ tức, Hủy niêm yết) hoặc cảnh báo từ danh sách dấu `*` hoặc `**`. Bên cạnh đó là Thống kê Dấu chân dòng tiền ngày hôm qua (khối lượng Mua Ròng / Bán Ròng từ Khối ngoại).
    *   **Bản tin Trưa & Chiều (Noon & Afternoon)**: 
        *   **Kịch biên độ**: Cảnh báo tức thời nếu mã nào chạm Trần / Sàn.
        *   **Biến động mạnh**: Liệt kê 3 mã Tăng mạnh nhất và 3 mã Giảm mạnh nhất (không trùng lặp với kịch biên độ) kèm Volume để phát hiện "kéo xả".
        *   **Top Thanh khoản**: liệt kê nhanh 3 mã có khối lượng giao dịch cao nhất trong ngày.
        *   **Khối ngoại (Mua/Bán Ròng)**: Theo sát dòng tiền mạnh nhất đổ vào hoặc rút ra khỏi thị trường.

---

## 2. 🧠 Thuật toán Spaced Repetition (SRS)
Hệ thống sử dụng thuật toán Lặp lại ngắt quãng dựa trên **Đường cong quên lãng của Ebbinghaus**.

### Bản chất của Đường cong quên lãng
Con người có xu hướng giảm bộ nhớ về một kiến thức mới học theo cấp số nhân trừ khi được ôn tập lại đúng lúc:
- **Sau 1 ngày**: Chỉ còn khoảng 33% kiến thức nếu không ôn tập.
- **SRS v1.2 giải quyết**: Ngắt quãng quá trình quên bằng cách ôn tập vào các mốc:
    - **Lần 1**: +1 ngày (Ngay sau khi học).
    - **Lần 2**: +3 ngày.
    - **Lần 3**: +7 ngày.
    - **Lần 4**: +30 ngày.
    - **Lần 5**: Ngẫu nhiên 60-90 ngày.
### Cấu trúc trí nhớ và Phân tầng ôn tập
Thuật toán phân tầng thời gian dựa trên mức độ ổn định của trí nhớ:
1. **Trí nhớ tạm thời (Short-term)**: Lần ôn 1 (+1 ngày).
2. **Trí nhớ trung hạn (Medium-term)**: Lần ôn 2 (+3 ngày) và Lần ôn 3 (+7 ngày).
3. **Trí nhớ dài hạn (Long-term)**: Lần ôn 4 (+30 ngày).
4. **Trí nhớ vĩnh viễn (Permanent)**: Lần ôn 5 (60-90 ngày).

---

## 3. 📁 Cấu trúc thư mục (Modular Design)
```text
assistant_v1.3/
├── main.py                # Điểm khởi chạy chính & Lập lịch (Scheduler)
├── config.py              # Cấu hình API Keys và IDs (Đọc từ .env)
├── modules/               # Thư mục chứa các module xử lý độc lập
│   ├── english.py         # Logic học Tiếng Anh (SRS & B2 Challenge)
│   ├── finance.py         # Lấy dữ liệu tài chính (Yahoo Finance)
│   ├── vn_finance.py      # Cào bảng điện chứng khoán Việt Nam (SCC)
│   ├── weather.py         # Lấy thông tin thời tiết (OpenWeatherMap)
│   ├── google_sheets.py   # Quản lý kết nối & cập nhật Sheets
│   └── notifier.py        # Gửi thông báo qua Telegram
├── scc/                   # Thư viện Chrome Controller điều khiển trình duyệt ẩn
├── samples/               # CSV templates để thiết lập Google Sheets ban đầu
└── requirements.txt       # Danh sách thư viện cần thiết
```

---

## 4. 🚀 Cài đặt & Sử dụng
### 1. Cài đặt thư viện
```bash
pip install -r requirements.txt
```
#### Thư viện cần thiết:
- `requests`: Lấy dữ liệu API thời tiết.
- `yfinance`: Truy xuất dữ liệu thị trường tài chính.
- `schedule`: Quản lý lập lịch gửi bản tin.
- `pytz`: Xử lý múi giờ địa phương.
- `google-auth`, `gspread`: Kết nối Google Sheets API.
- `python-dotenv`: Quản lý biến môi trường.
- *(Yêu cầu cài đặt Google Chrome & tải `chromedriver.exe` tương ứng vào thư mục gốc cho tính năng VN_Finance)*.

### 2. Cấu hình
- Copy `samples/.env.example` (nếu có) hoặc tạo file `.env` và điền thông tin (Bot Token, API Key...).
- Đặt file JSON Service Account của Google Cloud vào thư mục dự án.

### 3. Chuẩn bị Google Sheets
Sử dụng các file mẫu trong thư mục `/samples` để mồi dữ liệu (Header) cho các Sheet: `english_vocab`, `daily_fin`, `weather`, `vn_index` và cấp quyền chỉnh sửa cho tài khoản email của Google API. Nếu không có file mẫu vn_index, system sẽ tự đẻ cột dựa theo data scrape được.

### 4. Chạy ứng dụng
```bash
python main.py
```

---

## 5. 🛠 Gợi ý Khai thác Kho Dữ Liệu & Hướng phát triển (Advanced Roadmap)

Bằng việc tách chứng khoán Việt Nam ra thành môi trường Data Warehouse khép kín (không phụ thuộc yfinance), Assistant v1.3 mở ra hệ sinh thái chức năng mở rộng không giới hạn:

### Khai thác Dữ liệu Lịch sử (Backtesting & Analysis)
- **Tín hiệu Kỹ thuật Động (Dynamic Tech-signals)**: Khi cột dữ liệu `close` và `TotalVol` của từng mã đạt > 14 ngày trên Google Sheets, có thể code thêm hàm pandas tính RSI và MACD. Bot sẽ tự rà: "RSI của FPT xuống 28 (Quá bán) -> Bắn Telegram mua ngay".
- **Visual Chart (Vẽ biểu đồ)**: Dùng `matplotlib` để vẽ một biểu đồ đường (Line chart) biến động 1 tuần của 3 mã Top Tăng gửi dưới dạng **Ảnh** vào lúc 16:00.

### Tính năng Tương tác (Interactive Bot)
- Thay vì chỉ thụ động gửi tin, nâng cấp `notifier.py` sử dụng thư viện `python-telegram-bot` để nhận lệnh. Ví dụ người dùng gõ: `/check HPG`, Bot quét Google Sheets và báo lại giá HPG hiện tại cùng trend 3 ngày tới dựa vào Volume.

### Chiến thuật Cơ cấu / Tái lập danh mục
- Xây dựng file config `portfolio.json`. System sẽ check Google Sheets: Nếu mã trong danh mục giảm quá 7% (Hit Stoploss), ngay lập tức gửi cảnh báo khẩn cấp tới Telegram bất chấp giờ giao dịch.

---

## 6. 🛠 Yêu cầu Hệ thống
*   Python 3.10+
*   Google Cloud Service Account (Google Sheets API)
*   OpenWeatherMap API Key
*   Telegram Bot Token & Chat ID
*   Trình duyệt Chrome + ChromeDriver tương thích
*   Môi trường Terminal mã hóa UTF-8 (để không lỗi Emoji)
