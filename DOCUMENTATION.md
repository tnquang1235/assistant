# 🤖 Assistant v1.4 - Comprehensive Documentation

Assistant v1.4 là hệ thống trợ lý cá nhân tự động gửi bản tin hàng ngày qua Telegram. Hệ thống tích hợp dữ liệu từ nhiều nguồn (OpenWeatherMap, Yahoo Finance, Vietstock) và quản lý tiến trình học tập tiếng Anh thông qua Google Sheets.

---

## 1. 💡 Cấu trúc bản tin (Thứ tự gửi mỗi lần)
Bản tin Assistant được thiết kế theo triết lý **"Snapshot"**: hiển thị thông tin nhanh, gọn, chuyên nghiệp và tối ưu cho nhiều nền tảng, đặc biệt là Mobile (Telegram).

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
    *   **Kho dữ liệu (Google Sheets Data Warehouse)**: Do đặc thù dữ liệu chứng khoán Việt Nam khó lấy được lịch sử quá khứ chính xác qua API miễn phí, nên cần một "Kho dữ liệu" (Data warehouse) riêng biệt, và Google Sheets được sử dụng để lưu trữ dữ liệu. Dữ liệu được cào từ Vietstock trực tiếp trên bảng giá, sau đó sẽ được liên tục cập nhật/ghi đè đắp dần vào Google Sheets. Tính chất tự động mở rộng cột của phần mềm này cho phép cập nhật tới hơn 27 chỉ số (Giá Trực Tiếp, Volume, Khối ngoại mua/bán, v.v.). Cuối ngày (Afternoon), phiên bản ghi này sẽ chốt thành dữ liệu chính thức của ngày hôm đó.
    *   **Bản tin Sáng (Morning)**: Tập trung vào "chuẩn bị phiên mới". Hiển thị các sự kiện (Cổ tức, Hủy niêm yết) hoặc cảnh báo từ danh sách dấu `*` hoặc `**`. Bên cạnh đó là Thống kê Dấu chân dòng tiền ngày hôm qua (khối lượng Mua Ròng / Bán Ròng từ Khối ngoại).
    *   **Bản tin Trưa & Chiều (Noon & Afternoon)**: 
        *   **Kịch biên độ**: Cảnh báo tức thời nếu mã nào chạm Trần / Sàn.
        *   **Biến động mạnh**: Liệt kê 3 mã Tăng mạnh nhất và 3 mã Giảm mạnh nhất (không trùng lặp với kịch biên độ) kèm Volume để phát hiện "kéo xả".
        *   **Top Thanh khoản**: liệt kê nhanh 3 mã có khối lượng giao dịch cao nhất trong ngày.
        *   **Khối ngoại (Mua/Bán Ròng)**: Cập nhật dòng tiền mạnh nhất đổ vào hoặc rút ra khỏi thị trường.
    *   **📸 Cơ chế Chụp màn hình Lỗi (Visual Errors)**: Khi quá trình cào dữ liệu gặp sự cố (ví dụ: không tìm thấy bảng giá), hệ thống tự động chụp màn hình Chrome và gửi qua Telegram để chẩn đoán nguyên nhân nhanh chóng.
    *   **⚡ Tối ưu tốc độ tải**: Tăng thời gian chờ (Timeout) lên 30s và thêm cơ chế kiểm tra dữ liệu thực tế (ACB symbol check) để đảm bảo cào đủ dữ liệu ngay cả khi mạng chậm.
    *   **🔢 Quy tắc dữ liệu Atomic (Precision Extraction)**:
        *   **Cơ chế trích xuất**: Thay vì đọc trực tiếp nội dung văn bản hiển thị (vốn dễ bị lỗi dấu chấm/phẩy), hệ thống v1.4.0 sử dụng regex để trích xuất thuộc tính `data-value` từ DOM HTML. Đây là dữ liệu thô (raw data) từ máy chủ, đảm bảo chính xác 100%.
        *   **Luật xử lý dự phòng (10x Rule)**: Đối với các nguồn dữ liệu văn bản thô (nếu cần), hàm `parse_number` vẫn duy trì quy tắc nhân 10 (`44.35 -> 443.5`) và xử lý linh hoạt dấu thập phân dựa trên vị trí ký tự.
        *   **Hiển thị**: Giá được định dạng đơn vị `k` (VD: 27.5k) để tối ưu không gian tin nhắn.

---

## 2. 🏗️ Triết lý Thiết kế Job (Job Architecture Philosophy)
Để đảm bảo tính linh hoạt nhưng vẫn duy trì thói quen học tập bền bỉ, Assistant phân chia hệ thống Job thành 2 nhóm chính:

### A. Nhóm Job Cố định (Fixed Sessions)
*   **Thời gian**: Chạy vào 4 khung giờ vàng (06:00, 12:00, 16:00, 22:00).
*   **Tên gọi**: Được đặt định danh theo buổi (`Morning`, `Noon`, `Afternoon`, `Evening`).
*   **Đặc tính**:
    *   **Tính ổn định**: Tập trung vào việc xây dựng thói quen dài hạn cho người học.
    *   **Nội dung**: Bao gồm đầy đủ các Task (Chào hỏi, Thời tiết, Tiếng Anh, Tài chính).
    *   **Ràng buộc**: Task học Tiếng Anh bắt buộc gắn liền với tên buổi để khớp với cấu trúc `ENGLISH_CONFIG`, giúp người học nhận diện bài học theo nhịp sinh học hàng ngày.

### B. Nhóm Job Xen kẽ/Nhanh (Flexible Market Updates)
*   **Thời gian**: Linh động dựa trên diễn biến thị trường (08:00, 10:00...).
*   **Tên gọi**: Đặt theo bản chất nội dung báo cáo (ví dụ: `MARKET_OPENING`, `MARKET_WATCH`).
*   **Đặc tính**: Linh hoạt, không ràng buộc vào tên buổi, tập trung vào thị trường biến động mạnh.

---

## 3. 🧠 Thuật toán Spaced Repetition (SRS)
Hệ thống sử dụng thuật toán Lặp lại ngắt quãng dựa trên **Đường cong quên lãng của Ebbinghaus**.

### Bản chất của Đường cong quên lãng
Con người có xu hướng giảm bộ nhớ về một kiến thức mới học theo cấp số nhân trừ khi được ôn tập lại đúng lúc:
- **Sau 1 ngày**: Chỉ còn khoảng 33% kiến thức nếu không ôn tập.
- **SRS giải quyết**: Ngắt quãng quá trình quên bằng cách ôn tập vào các mốc:
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

### Tính bền bỉ và Logic Nhắc lại chuyên sâu
- **Recap thông minh**: Loại bỏ từ vựng vừa học trong chính phiên đó khỏi danh sách Recap để tối ưu vùng tin nhắn.
- **Tự chữa lành (Self-healing)**: Tự động tính toán lại lịch trình SRS cho các từ quá hạn (Overdue) ngay khi chúng xuất hiện trở lại.
- **Xử lý đa định dạng ngày**: Nhận diện linh hoạt `DD/MM/YYYY`, `YYYY-MM-DD` và tự động làm sạch khoảng trắng.
- **Thứ tự ưu tiên lấy từ (Anti-Collision)**: Hệ thống thực hiện lấy từ theo thứ tự: `Recap` -> `Old` -> `New`. Việc này đảm bảo các từ mới vừa bốc sẽ không bị trùng vào danh sách Recap của chính phiên đó, giúp phân tầng thông tin rõ ràng.

---

## 4. 📁 Cấu trúc thư mục (Modular Design)
```text
assistant/
├── main.py                # Điểm khởi chạy chính & Lập lịch (Scheduler)
├── config.py              # Cấu hình API Keys và IDs (Đọc từ .env)
├── modules/               # Thư mục chứa các module xử lý độc lập
│   ├── english.py         # Logic học Tiếng Anh (SRS & B2 Challenge)
│   ├── finance.py         # Lấy dữ liệu tài chính (Yahoo Finance)
│   ├── vn_finance.py      # Cào bảng điện VN (Tự động snapshot & parsing)
│   ├── weather.py         # Lấy thông tin thời tiết (OpenWeatherMap)
│   ├── google_sheets.py   # Quản lý kết nối & cập nhật Sheets
│   └── notifier.py        # Gửi thông báo Telegram (Hỗ trợ HTML & Gửi Ảnh)
├── scc/                   # Thư viện Chrome Controller điều khiển trình duyệt ẩn
├── samples/               # CSV templates để thiết lập Google Sheets ban đầu
└── requirements.txt       # Danh sách thư viện cần thiết
```

---

## 5. 🚀 Cài đặt & Sử dụng
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
- Copy `samples/.env.example` sang `.env` và điền thông tin.
- Đặt file JSON Service Account của Google Cloud vào thư mục dự án.

### 3. Chuẩn bị Google Sheets
Sử dụng các file mẫu trong thư mục `/samples` để mồi dữ liệu (Header) cho các Sheet: `english_vocab`, `daily_fin`, `weather`, `vn_index` và cấp quyền chỉnh sửa cho tài khoản email của Google API. 

### 4. Chạy ứng dụng
```bash
python main.py
```

---

## 6. 🛠 Cơ chế Chịu lỗi & Tối ưu hóa (Smart Resilience)
Nhằm đối phó với hạn mức (Quota) của Google Sheets API và lỗi mạng:

1.  **Ghi đè theo khối (Block Overwrite)**: Gom nhiều lần ghi cổ phiếu thành 01 lần gọi API duy nhất, giảm 90% tải.
2.  **Tự động xếp hàng & Thử lại (Auto-Retry)**: Pause 65s khi gặp lỗi Quota (429) và thử lại tự động.
3.  **📸 Visual Error Reporting**: Tích hợp SCC và Notifier để tự động gửi ảnh chụp trình duyệt khi gặp lỗi scraping (Timeout/Not Found).
4.  **Thứ tự ưu tiên Tài sản**: Tiếng Anh > Thời tiết > Tài chính.

---

## 7. 🔌 Tương thích Phần cứng & Đa nền tảng (Hardware Efficiency)
Hệ thống được tối ưu đặc biệt để chạy bền bỉ 24/7 trên các hệ thống tài nguyên thấp:

- **Hỗ trợ Headless/Raspberry Pi**: 
    - Toàn bộ các thư viện GUI (pymsgbox, tkinter) được chuyển sang cơ chế **Nạp chậm (Lazy Import)** và bọc trong khối xử lý lỗi.
    - Tự động phát hiện OS để chọn đường dẫn ChromeDriver phù hợp (`/usr/bin/chromedriver` trên Linux hoặc file `.exe` trên Windows).
- **Tối ưu hóa Tài nguyên**: 
    - Sử dụng bộ lọc dữ liệu thông minh để chỉ cập nhật Google Sheets khi có biến động giá thực sự.
    - Các lệnh `print` được loại bỏ Emoji (Unicode Clean-up) để tương thích tuyệt đối với Windows Terminal mặc định.

---

## 8. 🛡️ Triết lý Vận hành & Bảo trì (Maintenance Philosophy)
Quy trình xử lý lỗi tuân theo nguyên tắc "Ba tầng cảnh báo":

1.  **Tầng 1: Cảnh báo Telegram (Nhanh & Gọn)**: Giúp người dùng biết ngay lỗi cơ bản mà không cần đăng nhập vào máy chủ.
2.  **Tầng 2: Log Terminal (Chi tiết & Chuyên sâu)**: Phục vụ việc sửa lỗi phức tạp (Debug) khi người dùng đã remote vào máy chủ.
3.  **Tầng 3: Chẩn đoán bằng File Test (Xác định & Cách ly)**: Sử dụng các file test chuyên dụng như `test_vn_finance.py` để kiểm tra môi trường cô lập.

---

## 9. 🛠 Cấu hình Phân bổ Tiếng Anh (English Session Config)
Số lượng từ vựng được điều chỉnh linh hoạt theo từng buổi thông qua hằng số `ENGLISH_CONFIG` trong `main.py`:

| Buổi | Từ mới (New) | Ôn tập trong ngày (Recap) | Ôn tập ngày cũ (Old) |
| :--- | :---: | :---: | :---: |
| **Morning** | 2 | 0 | 5 |
| **Noon** | 2 | 2 | 5 |
| **Afternoon** | 1 | 4 | 5 |
| **Evening** | 0 | Tất cả | Tất cả |

---

## 10. 🛑 Các nguyên tắc quan trọng chỉnh sửa mã nguồn
1.  **Tuyệt đối không chỉnh sửa thư viện `scc`**: Đây là thư viện bên ngoài. 
2.  **Quy tắc lấy dữ liệu VN30**:
    - URL mặc định: `https://banggia.vietstock.vn/bang-gia/vn30`
    - Phải có tham số `VN30_PAGE_LOAD_WAIT` (ưu tiên 10 giây).
    - Kiểm tra trang đã load đủ bằng cách đếm dòng XPath `//tbody[@id="price-board-body"]/tr` (đủ 30 dòng).
    - **Chỉ lấy dữ liệu từ một bảng duy nhất** với cấu trúc XPath `//tbody[@id="price-board-body"]`.
3.  **Ưu tiên trên hết**: Tính ổn định, cấu trúc đơn giản để duy trì phần mềm dễ theo dõi và nâng cấp.

---

## 🧭 Tầm nhìn phát triển (Advanced Roadmap)
### Assistant - version 1.0
* Khai thác sự tiện dụng và đơn giản của Telegarm, giúp cung cấp cho người dùng những bản tin cập nhật nhanh chóng về những biến động của thời tiết, thị trường, nhắc nhở việc học tập.
* Đây cũng là quá trình giúp hình thành nên những ý tưởng và nguyên lý vận hành của dự án (back-end).
### Assistant - version 2.0
* Đây là phiên bản nâng cấp đáng kể về cách trình bày báo cáo và số liệu (font-end). Phiên bản nâng cấp đòi hỏi sự vận dụng nhiều công cụ Data Visualization, website,... để cung cấp thêm cho người dùng những báo cáo tổng quan và đa chiều về tình hình biến động đầy phức tạp của thị trường.
### Partner - Version 3.0
* Không còn là một trợ lý, phần mềm sẽ hoạt động như một cộng sự tin cậy (partner) của người dùng khi cung cấp được các số liệu hoặc báo cáo chuyên sâu, xử lý được các công việc phức tạp với độ linh hoạt và chính xác cao hơn. Sự tiến bộ của trí tuệ nhân tạo (AI) trong thời gian vừa qua đã cung cấp cho người dùng một viễn cảnh khả thi về một cộng sự thực thụ.

---

## 📊 Nhật ký Cập nhật (Changelog)

### v1.4.0 (2026-03-24)
- **Sửa lỗi nhắc từ tiếng Anh (SRS)**: Khắc phục lỗi lặp từ đa nghĩa.
- **Lấy dữ liệu VN30 tối ưu (Atomic DOM Snapshot)**: Chuyển sang cơ chế snapshot DOM và dùng regex trích xuất `data-value`.

### v1.3.x (2026-03-16)
- **Modularization**: Tái cấu trúc mã nguồn sang dạng Module.
- **VN-Index Data Warehouse**: Triển khai lưu trữ dữ liệu vào Google Sheets.
- **SRS Refinement**: Cải tiến thuật toán với cơ chế Recap thông minh.
