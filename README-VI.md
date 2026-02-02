# Bot CC Checker - Telegram Bot Kiểm Tra Thông Tin Thẻ

**Phiên bản:** 1.0.0  
**Ngôn ngữ:** [English](./README.md) | [Tiếng Việt](./README-VI.md)  
**Tác giả:** CTDOTEAM - Đỗ Thành #1110  
**Cập nhật lần cuối:** Tháng 2 năm 2026

---

## ⚠️ MIỄN TRỪ TRÁCH NHIỆM

Dự án này được cung cấp **NGUYÊN TRẠNG** mà không có bất kỳ bảo đảm hoặc cam kết nào. Tác giả và những người đóng góp **KHÔNG CHỊU TRÁCH NHIỆM** đối với:

- Bất kỳ hậu quả pháp lý hoặc vi phạm luật pháp phát sinh từ việc sử dụng công cụ này
- Mất dữ liệu, vi phạm bảo mật hoặc lỗi hệ thống
- Sử dụng sai mục đích thông tin thẻ tín dụng hoặc API xử lý thanh toán
- Vi phạm điều khoản dịch vụ của nhà cung cấp thanh toán
- Bất kỳ thiệt hại hoặc tổn thất phát sinh từ việc sử dụng phần mềm này

**Người dùng hoàn toàn chịu trách nhiệm** đảm bảo rằng việc sử dụng tuân thủ tất cả các luật pháp và quy định hiện hành.

---

## 📋 Tổng Quan

Một bot Telegram hiệu năng cao để kiểm tra thông tin thẻ tín dụng sử dụng BIN (Bank Identification Number) lookup và kiểm tra API. Bot cung cấp:

- Tra cứu thông tin thẻ theo thời gian thực (ngân hàng, quốc gia, loại thẻ)
- Xác minh BIN từ nhiều nguồn API
- Quản lý người dùng với cấp độ VIP
- Giới hạn sử dụng hàng ngày và bảo vệ thời gian chờ
- Kiểm soát quản trị viên và chế độ bảo trì
- Ghi nhật ký toàn diện và xử lý lỗi

---

## ✨ Tính Năng

### Tính Năng Cơ Bản
- **BIN Lookup**: Lấy ngân hàng, quốc gia, và loại thẻ từ 6-8 chữ số BIN
- **Hỗ trợ Đa API**: Luân phiên API cho dự phòng (system-api.pro, noxter.dev)
- **Thông Tin Quốc Gia**: Ánh xạ mã quốc gia, tên, và emoji cờ đầy đủ
- **Hiệu Năng Cao**: Kiến trúc async/await với connection pooling
- **Quản Lý Người Dùng**: Cấp độ VIP, giới hạn hàng ngày, theo dõi sử dụng

### Bảo Mật & Kiểm Soát
- Quản lý danh sách cho phép người dùng
- Thao tác chỉ dành cho quản trị viên
- Bảo vệ giới hạn tốc độ và thời gian chờ
- Chế độ bảo trì chỉ dành cho quản trị viên
- Cấu hình biến môi trường an toàn

### Ghi Nhật Ký & Giám Sát
- Ghi nhật ký toàn diện với dấu thời gian
- Thống kê sử dụng và phân tích
- Theo dõi lỗi và gỡ lỗi
- Nhật ký hoạt động để kiểm tra

---

## 🚀 Bắt Đầu Nhanh

### Yêu Cầu
- Python 3.8+
- pip trình quản lý gói
- Token Bot Telegram (lấy từ [@BotFather](https://t.me/botfather))

### Cài Đặt

1. **Sao chép kho lưu trữ**
   ```bash
   git clone https://github.com/yourusername/bot-check-cc.git
   cd bot-check-cc
   ```

2. **Tạo môi trường ảo**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Trên Windows: venv\Scripts\activate
   ```

3. **Cài đặt các phụ thuộc**
   ```bash
   pip install -r requirements.txt
   ```

4. **Cấu hình biến môi trường**
   ```bash
   cp .env.example .env
   # Chỉnh sửa .env với cấu hình của bạn
   ```

5. **Chạy bot**
   ```bash
   python bot.py
   ```

---

## ⚙️ Cấu Hình

### Biến Môi Trường (.env)

```env
# Bắt buộc
BOT_TOKEN=your_telegram_bot_token_here

# Tuỳ chọn - Khóa API
STRIPE_PUBLIC_KEY=pk_live_xxxxx
THUM_CONNECT_SID=your_thum_connect_sid
THUM_USER_ID=your_thum_user_id

# Quản Lý Người Dùng & Quản Trị Viên
ALLOWED_USERS=123456789,987654321
ADMIN_IDS=111111111,222222222
```

Xem [.env.example](./.env.example) để xem mẫu đầy đủ.

---

## 📁 Cấu Trúc Dự Án

```
bot-check-cc/
├── bot.py                 # Triển khai bot Telegram chính
├── config.py             # Quản lý cấu hình
├── api_client.py         # Máy khách API Stripe & Thum.io
├── bin_lookup.py         # BIN lookup với hỗ trợ đa API
├── database.py           # Quản lý cơ sở dữ liệu SQLite
├── user_agents.py        # Nhóm user agent xoay chiều
├── requirements.txt      # Phụ thuộc Python
├── .env.example          # Mẫu biến môi trường
├── .gitignore            # Quy tắc git ignore
├── README.md             # Tài liệu tiếng Anh
└── README-VI.md          # Tài liệu tiếng Việt (tập tin này)
```

---

## 🔍 Tính Năng BIN Lookup

Bot sử dụng lookup BIN thông minh với nhiều nguồn API:

### API Được Hỗ Trợ
1. **system-api.pro** - Nguồn API chính
2. **noxter.dev** - Nguồn API dự phòng

### Thông Tin Tra Cứu
Trả về thông tin thẻ sau:

```json
{
  "brand": "VISA",
  "type": "DEBIT",
  "level": "STANDARD",
  "bank": "Tên Ngân Hàng",
  "country_code": "VN",
  "country_name": "Vietnam",
  "country_flag": "🇻🇳",
  "prepaid": false
}
```

### Chiến Lược Luân Phiên API
- Mỗi yêu cầu bắt đầu từ một API khác để phân tán tải
- Tự động dự phòng sang API thay thế nếu một API bị lỗi
- Hợp nhất kết quả từ nhiều API để có thông tin đầy đủ
- Đảm bảo độ tin cậy và dự phòng dữ liệu

---

## 🛠️ Tham Chiếu API

### Mô-đun Chính

#### `bin_lookup.py`
Chức năng BIN lookup chính với ánh xạ quốc gia toàn diện.

**Hàm Chính:**
- `lookup_bin(bin_number)` - BIN lookup async với hỗ trợ đa API
- `format_bin_info(bin_info)` - Định dạng thông tin BIN để hiển thị

#### `api_client.py`
Tích hợp API Stripe và Thum.io với máy khách async hiệu năng cao.

**Phương Pháp Chính:**
- `check_card_quick(card_number, month, year, cvc)` - Xác thực thẻ nhanh

#### `config.py`
Quản lý cấu hình dựa trên biến môi trường.

**Cấu Hình:**
- BOT_TOKEN, khóa API, người dùng được phép, ID quản trị viên
- Điểm cuối URL cho dịch vụ API

#### `database.py`
Cơ sở dữ liệu SQLite để quản lý người dùng và thống kê.

**Bảng:**
- `users` - Hồ sơ người dùng với trạng thái VIP và giới hạn
- `settings` - Cài đặt bot toàn cầu

---

## 🧪 Kiểm Tra

### Kiểm Tra API BIN Lookup

```bash
# Sử dụng curl để kiểm tra system-api.pro
curl -s "https://system-api.pro/bin/559888"

# Sử dụng curl để kiểm tra noxter.dev
curl -s "https://noxter.dev/gate/bin?bin=559888"
```

### Kiểm Tra Thủ Công

```python
import asyncio
from bin_lookup import lookup_bin

async def test():
    result = await lookup_bin("559888")
    print(result)

asyncio.run(test())
```

---

## 📊 Thống Kê Sử Dụng

Bot theo dõi:
- Tổng số lần kiểm tra cho mỗi người dùng
- Sử dụng hàng ngày với tái đặt lại tự động
- Ngày hết hạn VIP
- Vai trò người dùng và quyền hạn

Truy cập qua lệnh `/stats` (chỉ dành cho quản trị viên).

---

## 🔐 Cân Nhắc Bảo Mật

- **Không bao giờ cam kết tập tin .env** - Sử dụng .env.example làm mẫu
- **Bảo vệ Bot Token** - Giữ BOT_TOKEN của bạn bí mật
- **Danh Sách Cho Phép Người Dùng** - Sử dụng ALLOWED_USERS và ADMIN_IDS
- **Giới Hạn Tốc Độ** - Bảo vệ thời gian chờ được tích hợp sẵn
- **Xác Thực Đầu Vào** - Xác thực định dạng BIN nghiêm ngặt
- **Khóa API** - Lưu trữ khóa nhạy cảm trong biến môi trường

---

## 🐛 Khắc Phục Sự Cố

### Bot Không Khởi Động
```bash
# Kiểm tra phiên bản Python
python --version  # Yêu cầu 3.8+

# Xác minh các phụ thuộc
pip list | grep -E "aiogram|aiohttp|python-dotenv"

# Kiểm tra tập tin .env tồn tại
test -f .env && echo "OK" || echo "Missing .env"
```

### BIN Lookup Lỗi
- Kiểm tra kết nối Internet
- Xác minh các điểm cuối API có thể truy cập:
  ```bash
  curl -s "https://system-api.pro/bin/559888" -o /dev/null -w "%{http_code}\n"
  curl -s "https://noxter.dev/gate/bin?bin=559888" -o /dev/null -w "%{http_code}\n"
  ```
- API có thể có giới hạn tốc độ hoặc hạn chế địa lý

### Lỗi Khóa Cơ Sở Dữ Liệu
```bash
# Xóa cơ sở dữ liệu bị hỏng
rm -f bot_users.db
# Bot sẽ tạo lại khi chạy tiếp theo
```

---

## 📦 Phụ Thuộc

Tất cả các phụ thuộc được liệt kê trong `requirements.txt`:

- **aiogram** (>=3.0.0) - Khung API Bot Telegram
- **aiohttp** (>=3.9.0) - Thư viện máy khách HTTP không đồng bộ
- **python-dotenv** (>=1.0.0) - Quản lý biến môi trường

---

## 📝 Giấy Phép & Ghi Công

**Bản quyền © CTDOTEAM - Đỗ Thành #1110**

Dự án này được cung cấp cho các mục đích giáo dục và kiểm tra được phép. Người dùng phải tuân thủ:
- Điều khoản dịch vụ API Telegram Bot
- Điều khoản API nhà cung cấp thanh toán (Stripe, v.v.)
- Quy định địa phương và quốc tế
- Các phương pháp công khai trách nhiệm

---

## 🤝 Đóng Góp

### Tiêu Chuẩn Mã
- Tuân theo hướng dẫn phong cách PEP 8
- Sử dụng gợi ý kiểu nơi áp dụng
- Thêm chuỗi tài liệu vào các hàm
- Bao gồm xử lý lỗi
- Kiểm tra trước khi gửi thay đổi

### Báo Cáo Vấn Đề
Vui lòng báo cáo lỗi hoặc yêu cầu tính năng qua GitHub Issues.

---

## 📞 Hỗ Trợ

Các câu hỏi, vấn đề hoặc thắc mắc:
- Kiểm tra tài liệu (README.md, README-VI.md)
- Xem phần khắc phục sự cố
- Mở GitHub Issue
- Liên hệ: CTDOTEAM - Đỗ Thành #1110

---

## 🔄 Cập Nhật & Bảo Trì

- Cập nhật thường xuyên cho khả năng tương thích API
- Các bản vá bảo mật khi cần
- Cập nhật phụ thuộc và phiên bản
- Tối ưu hóa hiệu suất

---

## 📚 Tham Chiếu

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [aiogram Documentation](https://docs.aiogram.dev/)
- [aiohttp Documentation](https://docs.aiohttp.org/)
- [BIN Database](https://en.wikipedia.org/wiki/Payment_card_number)

---

**Cập nhật lần cuối:** Tháng 2 năm 2026  
**Trạng thái:** Hoạt động  
**Phiên bản Python:** 3.8+

---

*Tài liệu này phục vụ như tài liệu chính trong tiếng Việt. Xem [README.md](./README.md) để xem phiên bản tiếng Anh.*
