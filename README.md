# ⚡ Agentic AI Trading System

> An autonomous crypto trading signal analysis system combining **Technical Analysis**, **Sentiment Analysis**, and **GPT-4o** through a **LangGraph Consensus Engine** — running entirely in the terminal.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/LangGraph-Consensus_Engine-blueviolet?logo=chainlink" />
  <img src="https://img.shields.io/badge/OpenAI-GPT--4o-412991?logo=openai&logoColor=white" />
  <img src="https://img.shields.io/badge/Binance-Futures_API-F0B90B?logo=binance&logoColor=black" />
  <img src="https://img.shields.io/badge/Docker-Supported-2496ED?logo=docker&logoColor=white" />
</p>

---

## 📖 Overview

**Agentic AI Trading System** is a complete agentic trading system built on a **multi-agent** architecture with an automated **consensus loop**. Five specialized agents work together to produce high-confidence trading signals:

1. **Technical Analyst Agent** — Computes RSI, MACD, Moving Averages, trend direction, and key support/resistance levels.
2. **Sentiment Analyzer Agent** — Reads and analyzes real-time market news to evaluate overall sentiment.
3. **Signal Generator Agent** — Synthesizes BUY/SELL/HOLD signals using rule-based logic from both sources above.
4. **OpenAI GPT-4o Agent** — Independently confirms or challenges the signal with in-depth reasoning.
5. **LangGraph Consensus Engine** — Orchestrates the entire pipeline, auto-retrying when agents disagree, and resolving conflicts with a safe fallback.

> ⚠️ This project is built for **research and learning purposes around Agentic AI Workflows**. It is not financial investment advice.

---

## 🎯 Key Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | **Rich Terminal UI** | Beautiful CLI with tables, progress bars, and color-coded output powered by `rich` |
| 2 | **Technical Analysis** | RSI(14), MACD, MA(20/50/200), Golden/Death Cross, auto-detected Support & Resistance |
| 3 | **Sentiment Analysis** | Market sentiment scoring from real-time news articles |
| 4 | **LangGraph Consensus** | Automated consensus loop with up to 3 retries when agents disagree |
| 5 | **GPT-4o Integration** | In-depth analysis with Entry Advice, Risk Management, and Market Context |
| 6 | **Live / Demo Mode** | Supports real Binance Futures data or randomly generated demo candles |
| 7 | **Auto-Analysis** | Scheduled re-analysis every 30s, 1m, 5m, 15m, or 30m — or run once on demand |
| 8 | **Docker Support** | Zero-setup deployment via Docker Compose |

---

## 🏗 System Architecture

```
                     ┌─────────────────────────────────────────────┐
                     │          LangGraph Consensus Engine          │
                     │                                              │
  CLI Input  ──────► │  load_data → technical_analysis             │
                     │                    ↓                         │
                     │            signal_generation                 │
                     │                    ↓                         │
                     │            openai_analysis                   │
                     │                    ↓                         │
                     │          consensus_check ── MATCH ──► finalize ──► Output
                     │                    │                         │
                     │               NO MATCH                       │
                     │                    ↓                         │
                     │       retry_count < 3? ─ YES ─► retry_openai ─► consensus_check
                     │                    │                         │
                     │                    NO                        │
                     │                    ↓                         │
                     │          force_finalize (with warning)       │
                     └─────────────────────────────────────────────┘
```

### Consensus Rules

| Technical Agent | GPT-4o Agent | Outcome |
|:-:|:-:|:--|
| BUY | BUY | ✅ **MATCH** — Finalize with +5% confidence bonus |
| SELL | SELL | ✅ **MATCH** — Finalize with +5% confidence bonus |
| HOLD | HOLD | ✅ **MATCH** — Finalize with +5% confidence bonus |
| BUY | HOLD | ❌ **MISMATCH** — Retry (up to 3 times) |
| SELL | HOLD | ❌ **MISMATCH** — Retry (up to 3 times) |
| BUY | SELL | ❌ **HARD CONFLICT** — Fallback to HOLD, confidence reduced by 40% |

---

## 📂 Project Structure

```
Agentic-AI-System/
├── .github/
│   └── workflows/
│       └── main.yml              # GitHub Actions CI/CD pipeline
├── src/
│   ├── agents/
│   │   ├── agent.py              # LangGraph Consensus Engine (core orchestrator)
│   │   ├── technical_analyst.py  # RSI, MACD, MA, trend, key levels
│   │   ├── sentiment_analyzer.py # News-based sentiment scoring
│   │   ├── signal_generator.py   # Rule-based BUY/SELL/HOLD signal synthesis
│   │   ├── openai_analyst.py     # GPT-4o agent for deep analysis
│   │   └── data_gatherer.py      # Market data collection utilities
│   ├── api/
│   │   └── schemas.py            # Pydantic models: OHLCV, MarketData, TradingSignal...
│   ├── utils/
│   │   └── api_clients.py        # External API connectors (News, Binance)
│   ├── logging/
│   │   └── logger.py             # Logging configuration
│   └── exception/
│       └── exception.py          # Custom exception handling
├── cli.py                        # CLI entry point — user interface
├── setup.py                      # Package setup
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Image build config
├── docker-compose.yml            # Docker Compose config
└── .env                          # API keys (never commit this)
```

---

## 🚀 Installation

### Requirements

- Python **3.10+**
- (Optional) Docker & Docker Compose

### 1. Clone the repository and create a virtual environment

```bash
git clone https://github.com/<your-username>/Agentic-AI-System.git
cd Agentic-AI-System

python3 -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt

# Recommended: install as a local package to resolve src.* imports
pip install -e .
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
# Binance Futures API (only required for Live Mode)
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret

# OpenAI (only required for GPT-4o Analysis & Consensus Engine)
OPENAI_KEY=your_openai_api_key
```

> **Note:** You can skip both keys entirely to run in **Demo Mode** without GPT-4o.

---

## 🖥 Usage

### Run locally

```bash
python3 cli.py
```

### Run with Docker

```bash
docker-compose run --rm agentic-cli
```

> Docker will automatically build the image (if not already built), connect your terminal to the CLI inside the container, and clean up on exit.

---

### CLI Walkthrough

The system prompts you step-by-step after launch:

#### 1. Select a trading pair
```
BTC/USDT  ETH/USDT  BNB/USDT  SOL/USDT  XRP/USDT
ADA/USDT  DOGE/USDT AVAX/USDT LINK/USDT DOT/USDT
```
Enter a number (1–10) or type a pair directly, e.g. `BTC/USDT`.

#### 2. Select a timeframe

| Key | Timeframe |
|:---:|:---------:|
| 1 | 1m |
| 2 | 5m |
| 3 | 15m |
| 4 | 1h |
| 5 | 4h |
| 6 | 1d |

#### 3. Select auto-analysis interval

| Key | Interval |
|:---:|:--------:|
| 1 | 30 seconds |
| 2 | 1 minute |
| 3 | 5 minutes |
| 4 | 15 minutes |
| 5 | 30 minutes |
| 6 | Run once only |

#### 4. Select data mode

- **Demo** — Generates simulated candles. No Binance API key required.
- **Live** — Pulls real-time data from Binance Futures. Requires API key.

#### 5. Enable / Disable GPT-4o (Consensus Engine)

- **Yes** — Activates the LangGraph Consensus Engine: GPT-4o cross-checks the Technical Agent's signal.
- **No** — Uses Technical Analysis + Sentiment Analysis only (faster, no OpenAI credit used).

---

## 📊 Sample Output

```
━━━━━━━ ⚡ AGENTIC AI TRADING  14:30:00 25/04/2026  🔴 LIVE  🤖 Consensus ━━━━━━━

┌──────────────────── 🤖 CONSENSUS ENGINE RESULT ──────────────────────┐
│  Trading Pair      BTC/USDT  1h                                       │
│  Current Price     65,432.10 USDT                                     │
│  Consensus Status  ✅ CONSENSUS REACHED                               │
│  Final Signal      BUY                                                │
│  Confidence        ████████████████░░░░ 82.5%                        │
│  Entry Zone        64,800.00 – 65,200.00                             │
│  Stop Loss         63,500.00                                          │
│  Take Profit       68,000.00                                          │
│  R:R Ratio         1 : 2.14                                           │
└───────────────────────────────────────────────────────────────────────┘

📊 Technical Indicators          🧠 Market Sentiment
┌─────────────────────┐          ┌───────────────────────┐
│ Trend    BULLISH    │          │ Label    BULLISH       │
│ RSI(14)  58.42      │          │ Score    0.72          │
│ MACD     +0.0032    │          │ Reason   Positive...   │
│ MA20     64,850     │          └───────────────────────┘
│ MA50     63,200     │
│ MA200    58,900     │
│ MA Cross Golden     │
│ Support  63,500     │
│ Resist.  67,000     │
└─────────────────────┘
```

---

## 🛠 Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError` | Dependencies missing or venv not activated | Run `source .venv/bin/activate` then `pip install -e .` |
| `OpenAI error` | Invalid API key or insufficient credits | Verify `OPENAI_KEY` in `.env` |
| `Binance error` → falls back to demo | Invalid key or network issue | Check Binance credentials or use Demo Mode |
| Unicode / emoji errors on Windows | Terminal encoding issue | The system auto-configures UTF-8; add `PYTHONUTF8=1` if the issue persists |
| `import src.*` fails | Package not installed | Run `pip install -e .` from the project root |

---

## 🤝 Contributing

Pull requests and issues are welcome. Please review the project structure and existing code conventions before contributing.

---

## 📄 License

See [LICENSE](LICENSE). This project is open-source for research and educational purposes on **Agentic AI Workflows**.
