# 🤖 Assistant v1.3 - Comprehensive Documentation

Assistant v1.3 là hệ thống trợ lý cá nhân tự động gửi bản tin hàng ngày qua Telegram. Hệ thống tích hợp dữ liệu từ nhiều nguồn (OpenWeatherMap, Yahoo Finance, Vietstock) và quản lý tiến trình học tập tiếng Anh thông qua Google Sheets.

---

## 1. 💡 Cấu trúc bản tin (Thứ tự gửi mỗi lần)
Bản tin Assistant v1.3 được thiết kế theo triết lý **"Snapshot"**: hiển thị thông tin nhanh, gọn, chuyên nghiệp và tối ưu cho nhiều nền tảng, đặc biệt là Mobile (Telegram).

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
            *   Cột **1D**: Lấy **2 số thập phân** (`.2f`) để cập nhật sát biến động (độ nhạy cao) hàng ngày.
            *   Các cột **1W, 1M, 1Q, 1Y**: Lấy **số nguyên** (`.0f`) để tối ưu không gian và xem nhanh xu hướng.
        *   **Cấu trúc kỹ thuật**: Sử dụng f-string `{giá_trị : [căn_lề][dấu][độ_rộng].[thập_phân][kiểu]}`. Ví dụ: `{:>+7.2f}%` cho cột 1D.
4.  **Chứng khoán Việt Nam (VN30 & Data Warehouse)**: 
    *   **Kho dữ liệu (Google Sheets Data Warehouse)**: Do đặc thù dữ liệu chứng khoán Việt Nam khó lấy được lịch sử quá khứ chính xác qua API miễn phí, nên cần một "Kho dữ liệu" (Data warehouse) riêng biệt, và Google Sheets được sử dụng để lưu trữ dữ liệu. Dữ liệu được cào xước từ Vietstock trực tiếp trên bảng giá, sau đó sẽ được liên tục cập nhật/ghi đè đắp dần vào Google Sheets. Tính chất tự động mở rộng cột của phần mềm này cho phép cập nhật tới hơn 27 chỉ số (Giá Trực Tiếp, Volume, Khối ngoại mua/bán, v.v.). Cuối ngày (Afternoon), phiên bản ghi này sẽ chốt thành dữ liệu chính thức của ngày hôm đó (các khung giờ buổi tối sẽ không thực hiện chạy lại dữ liệu).
    *   **Bản tin Sáng (Morning)**: Tập trung vào "chuẩn bị phiên mới". Hiển thị các sự kiện (Cổ tức, Hủy niêm yết) hoặc cảnh báo từ danh sách dấu `*` hoặc `**`. Bên cạnh đó là Thống kê Dấu chân dòng tiền ngày hôm qua (khối lượng Mua Ròng / Bán Ròng từ Khối ngoại).
    *   **Bản tin Trưa & Chiều (Noon & Afternoon)**: 
        *   **Kịch biên độ**: Cảnh báo tức thời nếu mã nào chạm Trần / Sàn.
        *   **Biến động mạnh**: Liệt kê 3 mã Tăng mạnh nhất và 3 mã Giảm mạnh nhất (không trùng lặp với kịch biên độ) kèm Volume để phát hiện "kéo xả".
        *   **Top Thanh khoản**: liệt kê nhanh 3 mã có khối lượng giao dịch cao nhất trong ngày.
        *   **Khối ngoại (Mua/Bán Ròng)**: Cập nhật dòng tiền mạnh nhất đổ vào hoặc rút ra khỏi thị trường.

---

## 2. 🏗️ Triết lý Thiết kế Job (Job Architecture Philosophy)
Để đảm bảo tính linh hoạt nhưng vẫn duy trì thói quen học tập bền bỉ, Assistant v1.3 phân chia hệ thống Job thành 2 nhóm chính:

### A. Nhóm Job Cố định (Fixed Sessions)
*   **Thời gian**: Chạy vào 4 khung giờ vàng (06:00, 12:00, 16:00, 22:00).
*   **Tên gọi**: Được đặt định danh theo buổi (`Morning`, `Noon`, `Afternoon`, `Evening`).
*   **Đặc tính**:
    *   **Tính ổn định**: Tập trung vào việc xây dựng thói quen dài hạn cho người học.
    *   **Nội dung**: Bao gồm đầy đủ các Task (Chào hỏi, Thời tiết, Tiếng Anh, Tài chính).
    *   **Ràng buộc**: Task học Tiếng Anh bắt buộc gắn liền với tên buổi để khớp với cấu trúc `ENGLISH_CONFIG`, giúp người học nhận diện bài học theo nhịp sinh học hàng ngày.

### B. Nhóm Job Xen kẽ/Nhanh (Flexible Market Updates)
*   **Thời gian**: Linh động dựa trên diễn biến thị trường (ví dụ: 08:00, 10:00, hoặc các giờ cao điểm giao dịch).
*   **Tên gọi**: Đặt theo bản chất nội dung báo cáo (ví dụ: `MARKET_OPENING`, `MARKET_WATCH`, `PRE_MARKET`).
*   **Đặc tính**:
    *   **Tính linh hoạt**: Không ràng buộc vào tên buổi, cho phép người dùng tùy chỉnh báo cáo (Full/Highlights) và thời gian nhận tin bất cứ lúc nào.
    *   **Nội dung**: Thường chỉ tập trung vào các thị trường biến động mạnh (VN-Index, Crypto, v.v.).
    *   **Khai báo biến**: Sử dụng các biến tạp, biến trung gian độc lập để điều phối dữ liệu mà không làm ảnh hưởng đến cấu trúc học tập của các Session cố định.

---

## 3. 🧠 Thuật toán Spaced Repetition (SRS)
Hệ thống sử dụng thuật toán Lặp lại ngắt quãng dựa trên **Đường cong quên lãng của Ebbinghaus**.

### Bản chất của Đường cong quên lãng
Con người có xu hướng giảm bộ nhớ về một kiến thức mới học theo cấp số nhân trừ khi được ôn tập lại đúng lúc:
- **Sau 1 ngày**: Chỉ còn khoảng 33% kiến thức nếu không ôn tập.
- **SRS v1.3 giải quyết**: Ngắt quãng quá trình quên bằng cách ôn tập vào các mốc:
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

### Tính bền bỉ và Logic Nhắc lại chuyên sâu (Recap & Robustness)
Assistant v1.3 cải tiến khả năng xử lý dữ liệu học tập với độ tin cậy cực cao:
- **Recap thông minh (No Redundancy)**: Trong cùng một bản tin, hệ thống sẽ ưu tiên nạp danh sách Recap từ các buổi học *trước đó* trong cùng ngày. Những từ mới vừa bốc trong chính buổi hiện tại sẽ không bị lặp lại ở phần Recap để tiết kiệm diện tích vùng tin nhắn.
- **Tự chữa lành dữ liệu (Self-healing Overdue)**: Nếu một từ bị "nợ" (quá hạn ôn tập) do lỗi hệ thống hoặc do người dùng bỏ lỡ, ngay khi được nhắc lại, lịch trình SRS của từ đó sẽ được tính toán lại dựa trên thời điểm hiện tại. Điều này giúp đưa từ vựng trở lại đúng chu kỳ mà không cần can thiệp thủ công vào cơ sở dữ liệu.
- **Cơ chế bỏ qua từ vựng (Skip Empty Reviews)**: Nếu cột `next_review` bị để trống trên Google Sheets, hệ thống sẽ coi đó là từ không cần ôn tập và hoàn toàn bỏ qua, giúp người dùng linh hoạt quản lý danh mục từ vựng "Mastered" hoặc "Ignored".
- **Xử lý đa định dạng ngày (Flexible Date Parsing)**: Hệ thống tự động nhận diện và chuyển đổi linh hoạt giữa các định dạng ngày `DD/MM/YYYY`, `YYYY-MM-DD` hoặc `DD-MM-YYYY`. Ngoài ra, cơ chế `.strip()` được áp dụng triệt để để loại bỏ các khoảng trắng thừa do lỗi nhập liệu của người dùng.
- **Kiểm thử tự động (Quality Assurance)**: Dự án tích hợp các bộ công cụ kiểm thử như `test_english_recap.py`, `diagnostic_english.py` và `test_telegram_english.py` để đảm bảo logic luôn chạy đúng trước khi gửi tin thực tế.

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

### Cơ chế Chịu lỗi & Tối ưu hóa API (Smart Resilience)
Nhằm đối phó với hạn mức (Quota) nghiêm ngặt của Google Sheets API (60 requests/phút), Assistant v1.3 triển khai 4 lớp bảo mật dữ liệu:

1.  **Ghi đè theo khối (Block Overwrite)**: Thay vì cập nhật từng dòng cổ phiếu (30 lần API call), hệ thống sẽ tính toán dải hàng (Range) từ hàng đầu tiên đến hàng cuối cùng có sự thay đổi. Toàn bộ khối dữ liệu này được ghi đè trong **duy nhất 01 lần gọi API**. Hệ thống đã được hiệu chỉnh để tự động ép kiểu dữ liệu (`object casting`), tránh lỗi xung đột giữa số nguyên (int64) và số thập phân (gold prices/indices).
2.  **Tự động xếp hàng & Thử lại (Auto-Retry)**: Khi gặp lỗi `429 (Quota Exceeded)`, hệ thống sẽ tự động tạm dừng 65 giây để reset quota, sau đó tự động thực hiện lại lệnh ghi (tối đa 2 lần).
3.  **Thông báo sự cố qua Telegram**: Mọi trạng thái "đang xếp hàng chờ API" hoặc lỗi ghi nghiêm trọng đều được gửi trực tiếp tới Telegram của người dùng để kịp thời nắm bắt trạng thái của Data Warehouse.
4.  **Thứ tự ưu tiên Tài sản (Asset Priority)**: Logic thực thi theo thứ tự: **Tiếng Anh (Quan trọng nhất)** -> Thời tiết -> Tài chính. Dữ liệu giáo dục luôn được đảm bảo an toàn nếu hạn mức API cạn kiệt ở cuối ca.

---

## 6. 🔌 Tương thích Phần cứng & Đa nền tảng (Hardware Efficiency)
Assistant v1.3 được tối ưu đặc biệt để chạy bền bỉ 24/7 trên các hệ thống tài nguyên thấp:

- **Hỗ trợ Headless/Raspberry Pi**: 
    - Toàn bộ các thư viện GUI (pymsgbox, tkinter) được chuyển sang cơ chế **Nạp chậm (Lazy Import)** và bọc trong khối xử lý lỗi. Điều này giúp Bot khởi động mượt mà trên môi trường Linux Server/Docker/Raspberry Pi mà không bị treo do thiếu trình quản lý cửa sổ.
    - Tự động phát hiện OS để chọn đường dẫn ChromeDriver phù hợp (`/usr/bin/chromedriver` trên Linux hoặc file `.exe` trên Windows).
- **Tối ưu hóa Tài nguyên**: 
    - Sử dụng bộ lọc dữ liệu thông minh để chỉ cập nhật Google Sheets khi có biến động giá thực sự, giúp giảm tải CPU và băng thông mạng.
    - Các lệnh `print` được loại bỏ Emoji (Unicode Clean-up) để tương thích tuyệt đối với Windows Terminal mặc định, tránh lỗi `UnicodeEncodeError`.

---

## 6. 🛠 Yêu cầu Hệ thống
*   Python 3.10+
*   Google Cloud Service Account (Google Sheets API)
*   OpenWeatherMap API Key
*   Telegram Bot Token & Chat ID
*   Trình duyệt Chrome + ChromeDriver tương thích
*   Môi trường Terminal mã hóa UTF-8 (để không lỗi Emoji)
