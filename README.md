# Agentic AI Trading System ⚡

Hệ thống giao dịch tự động bằng AI, phân tích thị trường dựa trên các chỉ số kỹ thuật và tâm lý thị trường thông qua CLI (Command Line Interface).

Hệ thống sử dụng **GPT-4o** (tùy chọn) để đưa ra các nhận định chuyên sâu dựa trên sự hội tụ (confluence) của tín hiệu kỹ thuật (Technical Analysis) và tín hiệu tâm lý (Sentiment Analysis) thu thập từ tin tức thị trường thực tế.

---

## 🎯 Tính năng nổi bật

1. **Giao diện CLI mạnh mẽ**: Sử dụng thư viện `rich` để hiển thị các bảng dữ liệu, chỉ báo kỹ thuật, và tiến trình đếm ngược sinh động ngay trên terminal.
2. **Technical Analysis Agent**: Tự động tính toán các chỉ báo kỹ thuật quan trọng:
   - Xu hướng hiện tại (BULLISH/BEARISH/NEUTRAL)
   - RSI (14)
   - MACD
   - Moving Averages (MA20, MA50, MA200) và MA Cross (Golden/Death Cross)
   - Các mức Kháng cự (Resistance) / Hỗ trợ (Support)
3. **Sentiment Analysis Agent**: Thu thập và phân tích các tin tức thị trường để đánh giá tâm lý chung.
4. **OpenAI GPT-4o Integration**: Phân tích chuyên sâu từ AI, đưa ra hành động cụ thể, lời khuyên vào lệnh (entry advice), và quản lý rủi ro (risk advice).
5. **Real-time Live Data & Demo Mode**: 
   - **Live**: Kéo dữ liệu thực từ Binance Futures.
   - **Demo**: Chạy bằng dữ liệu giả lập có độ biến động tương tự thực tế.
6. **Auto-Analysis Interval**: Lên lịch tự động cập nhật và phân tích dữ liệu sau mỗi khoảng thời gian định trước (vd: 30 giây, 1 phút, 5 phút, ...).

---

## 🚀 Hướng dẫn cài đặt

### 1. Cài đặt Python và tạo môi trường ảo

Yêu cầu: Python 3.10+

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Cài đặt Dependencies

```bash
pip install -r requirements.txt
```

### 3. Cấu hình biến môi trường (`.env`)

Tạo file `.env` ở thư mục gốc của dự án và điền các API key của bạn:

```env
# Binance (dành cho Live Mode)
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret

# OpenAI (dành cho GPT-4o Analysis)
OPENAI_KEY=your_openai_api_key
```

> **Lưu ý:** Bạn có thể chạy chế độ **Demo** và bỏ qua `OPENAI_KEY` nếu chỉ muốn xem thuật toán kỹ thuật hoạt động. 

---

## 🖥 Hướng dẫn sử dụng

### Chạy trực tiếp (Local)
Chạy hệ thống bằng lệnh:

```bash
python3 cli.py
```

### Chạy bằng Docker
Bạn có thể khởi chạy ứng dụng hoàn toàn thông qua Docker. Vì đây là CLI yêu cầu tương tác (nhập thông số), hãy sử dụng lệnh sau:

```bash
docker-compose run --rm agentic-cli
```
> Khi sử dụng lệnh này, Docker sẽ build image (nếu chưa có), chạy container, kết nối terminal của bạn với CLI bên trong container và tự động dọn dẹp (xóa container) khi bạn thoát.

### Cấu hình trong CLI:

1. **Chọn cặp giao dịch**: Nhập số tương ứng với cặp giao dịch (vd: BTC/USDT, ETH/USDT, SOL/USDT...). Hoặc bạn có thể gõ trực tiếp tên cặp như `BTC/USDT`.
2. **Chọn khung thời gian (Timeframe)**: Lựa chọn khung thời gian để phân tích (1m, 5m, 15m, 1h, 4h, 1d).
3. **Tự động phân tích theo chu kỳ**: 
   - Nếu bạn chọn chu kỳ (vd: `30 giây`), hệ thống sẽ tự động cập nhật dữ liệu và phân tích lại sau mỗi 30 giây. 
   - Nếu chọn `Chỉ chạy 1 lần`, hệ thống sẽ phân tích xong rồi đợi bạn ấn `Enter` để phân tích tiếp.
4. **Dùng GPT-4o**: 
   - Bạn có thể bật tính năng này để gọi OpenAI phân tích chuyên sâu các chỉ số kỹ thuật và tâm lý, đưa ra **Signal**, **Entry**, và **Risk management**.
5. **Chế độ dữ liệu**:
   - `Demo`: Dữ liệu sinh ngẫu nhiên, không cần kết nối API Binance.
   - `Live`: Kéo dữ liệu thực từ Binance Futures.

---

## 📂 Cấu trúc thư mục

```
Agentic-AI-System/
├── .github/
│   └── workflows/
│       └── main.yml           # GitHub Actions CI/CD Pipeline
├── Dockerfile                 # File build image cho hệ thống
├── docker-compose.yml         # File cấu hình khởi chạy Docker dễ dàng
├── cli.py                     # Entry point chính của hệ thống CLI
├── requirements.txt           # File cài đặt thư viện
├── .env                       # Chứa API keys (không push lên git)
├── src/
│   ├── agents/
│   │   ├── technical_analyst.py   # Phân tích kỹ thuật (RSI, MACD, MA...)
│   │   ├── sentiment_analyzer.py  # Phân tích tâm lý thị trường
│   │   ├── signal_generator.py    # Tổng hợp tín hiệu (Rule-based)
│   │   └── openai_analyst.py      # OpenAI GPT-4o Agent
│   ├── api/
│   │   └── schemas.py             # Pydantic schemas lưu trữ dữ liệu nội bộ
│   ├── utils/
│   │   └── api_clients.py         # Kết nối APIs ngoài (News, Binance)
│   └── logging/
│       └── logger.py              # Xử lý ghi log
└── README.md                  # File tài liệu hướng dẫn
```

---

## 🛠 Troubleshooting

- **Lỗi `OpenAI error`:** Đảm bảo `OPENAI_KEY` trong file `.env` chính xác và tài khoản OpenAI của bạn còn credit.
- **Lỗi kết nối Binance:** Hãy kiểm tra lại kết nối mạng hoặc thử chạy ở chế độ **Demo** để xác nhận hệ thống logic vẫn bình thường.
- **Lỗi `ModuleNotFoundError`:** Đảm bảo bạn đã kích hoạt virtual environment (`source .venv/bin/activate`) và đã chạy `pip install -r requirements.txt`.

---

## 🤝 Giấy phép
Project phục vụ mục đích nghiên cứu và tham khảo về Agentic Workflow. Không phải lời khuyên đầu tư tài chính.
