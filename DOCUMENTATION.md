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
4.  **Chứng khoán Việt Nam (Lộ trình phát triển)**: 
    *   **Theo dõi chỉ số**: VN-Index, HNX-Index và các nhóm ngành nổi bật.
    *   **Dòng tiền**: Top 5 cổ phiếu thanh khoản cao nhất phiên.
    *   **Phân tích kỹ thuật**: Cảnh báo vùng quá mua/quá bán (RSI) hoặc cắt lên/cắt xuống (MACD).
    *   **Dữ liệu**: Tích hợp API chứng khoán (SSI, VNDirect hoặc các nguồn tương đương).

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
assistant_v1.2/
├── main.py                # Điểm khởi chạy chính & Lập lịch (Scheduler)
├── config.py              # Cấu hình API Keys và IDs (Đọc từ .env)
├── modules/               # Thư mục chứa các module xử lý độc lập
│   ├── english.py         # Logic học Tiếng Anh (SRS & B2 Challenge)
│   ├── finance.py         # Lấy dữ liệu tài chính (Yahoo Finance)
│   ├── weather.py         # Lấy thông tin thời tiết (OpenWeatherMap)
│   ├── google_sheets.py   # Quản lý kết nối & cập nhật Sheets
│   └── notifier.py        # Gửi thông báo qua Telegram
├── samples/               # CSV templates để thiết lập Google Sheets
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

### 2. Cấu hình
- Copy `.env.example` thành `.env` và điền thông tin (Bot Token, API Key...).
- Đặt file JSON Service Account của Google Cloud vào thư mục dự án.
### 3. Chuẩn bị Google Sheets
Sử dụng các file mẫu trong thư mục `/samples` để thiết lập các Sheet: `english_vocab`, `daily_fin`, `weather` và cấp quyền chỉnh sửa cho tài khoản email của Google API.
### 4. Chạy ứng dụng
```bash
python main.py
```

---

## 5. 🛠 Yêu cầu Hệ thống
*   Python 3.10+
*   Google Cloud Service Account (Google Sheets API)
*   OpenWeatherMap API Key
*   Telegram Bot Token & Chat ID
*   Yfinance (Thư viện lấy dữ liệu tài chính)


## 6. 🛠 Hướng phát triển tiếp theo
*   Version 1.3: Lấy dữ liệu chứng khoán Việt Nam. Không có API miễn phí tốt cho thị trường Việt Nam, nên phải sử dụng thư viện SCC để thu thập dữ liệu từ các website chứng khoản.
*   Version 1.4: Đọc tin nhắn của người dùng gửi đến BOT Telegram để thực hiện các lệnh như: cập nhật thị trường, cập nhật từ vựng, v.v.
*   Version 1.5: Tổng hợp dữ liệu báo cáo (bằng văn bản) các chỉ số kinh tế như: GDP, CPI,....
*   Version 1.6: Sử dụng AI để tóm tắt tin tức và phân tích thị trường.
