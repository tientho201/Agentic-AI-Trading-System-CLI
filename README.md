# Crypto AI Agent System

Một hệ thống AI đa đặc vụ (Multi-Agent System) tự động thu thập dữ liệu thị trường tiền điện tử (Crypto), phân tích tâm lý đám đông, phân tích kỹ thuật và đưa ra các cảnh báo/tín hiệu giao dịch (ví dụ: dự đoán vùng đỉnh, đáy).

## Kiến trúc Hệ thống (Agents)

Hệ thống được thiết kế với nhiều Agent đóng các vai trò khác nhau, phối hợp với nhau thông qua một Orchestrator:

1. **Data Gatherer Agent** (`src/agents/data_gatherer.py`):
   - Chịu trách nhiệm cào dữ liệu (scrape/fetch) từ các nguồn tin tức (CoinDesk, CryptoPanic), mạng xã hội (Twitter, Reddit, Telegram) và dữ liệu giá/volume từ sàn giao dịch (Binance, CoinGecko).
2. **Sentiment Analyzer Agent** (`src/agents/sentiment_analyzer.py`):
   - Phân tích ngôn ngữ tự nhiên (NLP) trên các dữ liệu chữ (text) thu thập được để chấm điểm tâm lý thị trường (Bullish, Bearish, Neutral, F&G Index).
3. **Technical Analyst Agent** (`src/agents/technical_analyst.py`):
   - Phân tích biểu đồ và các chỉ báo kỹ thuật (RSI, MACD, Bollinger Bands, Volume Profile...) dựa trên dữ liệu giá (OHLCV).
4. **Signal Generator Agent** (`src/agents/signal_generator.py`):
   - Đóng vai trò là "Người ra quyết định". Tổng hợp kết quả từ Sentiment và Technical để đưa ra tín hiệu cảnh báo (Mua/Bán, Cảnh báo vùng đỉnh/đáy, Rủi ro thanh lý).
5. **Orchestrator** (`src/core/orchestrator.py`):
   - Bộ điều phối chính, quản lý luồng dữ liệu giữa các Agent, lưu trữ ngữ cảnh ngắn hạn/dài hạn (Memory) và lập lịch chạy (scheduler).

## Cấu trúc Thư mục Hiện Tại

```text
Agentic_AI_System/
├── .github/                    # Chứa file CI/CD workflows
├── data/                       # Thư mục chứa dữ liệu tĩnh (raw/processed)
├── data_schema/                # Định nghĩa schema cấu trúc dữ liệu
│   └── schema.yaml             # Schema chuẩn hóa
├── src/                        # Chứa toàn bộ source code của dự án
│   ├── agents/                 # Logic của từng Agent cụ thể
│   │   ├── data_gatherer.py
│   │   ├── sentiment_analyzer.py
│   │   ├── signal_generator.py
│   │   └── technical_analyst.py
│   ├── api/                    # Cung cấp API (FastAPI) để giao tiếp bên ngoài
│   │   ├── routes.py
│   │   └── schemas.py
│   ├── config/                 # File cấu hình ứng dụng
│   │   └── settings.yaml
│   ├── core/                   # Lõi điều phối hệ thống
│   │   ├── memory.py           # Lưu trữ ngữ cảnh/Vector DB
│   │   └── orchestrator.py     # Điều phối các agents
│   ├── pipeline/               # Định nghĩa các luồng xử lý/pipeline CI/ML
│   ├── tests/                  # Unit tests và integration tests
│   └── utils/                  # Tiện ích dùng chung
│       ├── api_clients.py
│       └── logger.py
├── .env                        # Biến môi trường (API Keys, config local)
├── .gitignore                  # File loại trừ git
├── docker-compose.yml          # Cấu hình multi-container (DB, app)
├── Dockerfile                  # Đóng gói app
├── main.py                     # Entry point chạy ứng dụng
├── README.md                   # Tài liệu dự án
└── requirements.txt            # Thư viện phụ thuộc
```

## Hướng dẫn cài đặt (Getting Started)

### 1. Yêu cầu hệ thống

- Python 3.9+
- Khuyến nghị dùng môi trường ảo (Virtual Environment) như `venv` hoặc `conda`.

### 2. Cài đặt

Clone hoặc di chuyển vào thư mục dự án:

```bash
cd Agentic_AI_System
```

Tạo và kích hoạt môi trường ảo:

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# MacOS/Linux:
source venv/bin/activate
```

Cài đặt các thư viện phụ thuộc:

```bash
pip install -r requirements.txt
```

### 3. Cấu hình biến môi trường

Tạo file `.env` (nếu chưa có) và điền các API Key của bạn (OpenAI, Binance, Twitter...):

```env
OPENAI_API_KEY=sk-your-openai-key-here
BINANCE_API_KEY=your-binance-key
BINANCE_SECRET_KEY=your-binance-secret
TWITTER_BEARER_TOKEN=your-twitter-token
```

### 4. Chạy hệ thống

Để khởi động hệ thống, chạy file `main.py`:

```bash
python main.py
```

## Các bước tiếp theo (Roadmap)

- [ ] Hoàn thiện `data_schema/schema.yaml` để chuẩn hóa dữ liệu đầu ra từ các nguồn.
- [ ] Implement `src/agents/data_gatherer.py` tích hợp CCXT để lấy giá từ Binance và API báo chí.
- [ ] Tích hợp LLM (như GPT-4 hoặc Claude) vào `src/agents/sentiment_analyzer.py` qua LangChain/LlamaIndex.
- [ ] Viết thuật toán cho `src/agents/technical_analyst.py`.
- [ ] Thiết kế logic tổng hợp cho `src/agents/signal_generator.py`.
- [ ] Cài đặt API endpoints trong `src/api/routes.py` để UI/Bot có thể kết nối.
- [ ] Thiết lập thông báo qua Telegram Bot ở `main.py` hoặc luồng pipeline.
