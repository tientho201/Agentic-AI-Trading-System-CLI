#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agentic AI Trading CLI
Tuong tac voi he thong phan tich tin hieu qua terminal.
"""
import sys
import os
import time
import signal

# Force UTF-8 encoding for all output — fix UnicodeEncodeError with emoji
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

# Dam bao import dung path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.rule import Rule
from rich import box
from datetime import datetime

console = Console()

# ── Constants ────────────────────────────────────────────────────────────────

SYMBOLS = [
    "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT",
    "ADA/USDT", "DOGE/USDT", "AVAX/USDT", "LINK/USDT", "DOT/USDT"
]

TIMEFRAMES = {
    "1": ("1m",  "1 Phút"),
    "2": ("5m",  "5 Phút"),
    "3": ("15m", "15 Phút"),
    "4": ("1h",  "1 Giờ"),
    "5": ("4h",  "4 Giờ"),
    "6": ("1d",  "1 Ngày"),
}

INTERVALS = {
    "1": (30,   "30 giây"),
    "2": (60,   "1 phút"),
    "3": (300,  "5 phút"),
    "4": (900,  "15 phút"),
    "5": (1800, "30 phút"),
    "6": (0,    "Chỉ chạy 1 lần"),
}

# ── Helpers ──────────────────────────────────────────────────────────────────

def clear():
    os.system("clear" if os.name == "posix" else "cls")

def banner():
    console.print(Panel.fit(
        "[bold cyan]⚡ AGENTIC AI TRADING SYSTEM[/bold cyan]\n"
        "[dim]Phân tích kỹ thuật & tâm lý thị trường bằng AI[/dim]",
        border_style="cyan", padding=(1, 4)
    ))

def _signal_color(action: str) -> str:
    return {"BUY": "green", "SELL": "red", "HOLD": "yellow"}.get(action, "white")

def _trend_color(trend: str) -> str:
    return {"BULLISH": "green", "BEARISH": "red", "NEUTRAL": "yellow"}.get(trend, "white")

def _rsi_label(rsi: float) -> str:
    if rsi > 70: return "[red]Overbought[/red]"
    if rsi < 30: return "[green]Oversold[/green]"
    return "[white]Normal[/white]"

def _conf_bar(conf: float, width: int = 20) -> str:
    filled = int(conf * width)
    bar = "█" * filled + "░" * (width - filled)
    color = "green" if conf >= 0.7 else "yellow" if conf >= 0.4 else "red"
    return f"[{color}]{bar}[/{color}] {conf*100:.1f}%"

def fmt(val, decimals=2):
    if val is None: return "--"
    v = float(val)
    if v == 0: return "--"
    if v > 1000: return f"{v:,.{decimals}f}"
    if v > 1:    return f"{v:.4f}"
    return f"{v:.6f}"

def load_data(symbol: str, timeframe: str, use_live: bool):
    """Tải dữ liệu nến và tin tức."""
    import random, math

    if use_live:
        try:
            from binance.client import Client
            client = Client(
                api_key=os.getenv("BINANCE_API_KEY", ""),
                api_secret=os.getenv("BINANCE_API_SECRET", "")
            )
            sym = symbol.replace("/", "").upper()
            klines = client.futures_klines(symbol=sym, interval=timeframe, limit=200)
            candles = [{
                "timestamp": int(k[0]), "open": float(k[1]), "high": float(k[2]),
                "low": float(k[3]), "close": float(k[4]), "volume": float(k[5])
            } for k in klines]
        except Exception as e:
            console.print(f"[yellow]⚠ Binance lỗi ({e}), dùng demo data[/yellow]")
            use_live = False

    if not use_live:
        seed = {"BTC": 65000, "ETH": 3200, "BNB": 580, "SOL": 175,
                "XRP": 0.55, "ADA": 0.45, "DOGE": 0.18, "AVAX": 38}.get(symbol.split("/")[0], 100)
        price, candles = seed, []
        now = int(time.time() * 1000)
        for i in range(200):
            price *= (1 + random.uniform(-0.012, 0.015))
            o = price * random.uniform(0.998, 1.002)
            h = max(o, price) * random.uniform(1.001, 1.01)
            l = min(o, price) * random.uniform(0.990, 0.999)
            candles.append({"timestamp": now - (200 - i) * 3_600_000,
                            "open": round(o, 6), "high": round(h, 6),
                            "low": round(l, 6), "close": round(price, 6),
                            "volume": round(random.uniform(100, 5000), 2)})

    # Tin tức
    news = []
    if use_live:
        try:
            from src.utils.api_clients import FreeNewsDay
            raw = FreeNewsDay().get_recent_news(symbol=symbol, limit=5)
            for n in raw:
                news.append({
                    "title": str(n.get("title", "")),
                    "source": str(getattr(n.get("source", ""), "name", n.get("source", ""))),
                    "published_at": str(n.get("published_at", "")),
                })
        except Exception:
            pass

    if not news:
        b = symbol.split("/")[0]
        news = [
            {"title": f"{b} institutional adoption surge", "source": "CryptoNews", "published_at": "now"},
            {"title": f"Major partnership boosts {b}", "source": "CoinDesk", "published_at": "now"},
        ]

    return candles, news

def run_analysis(symbol: str, timeframe: str, use_live: bool):
    """Chạy pipeline qua LangGraph Consensus Engine."""
    from src.agents.agent import run_agent

    candles, news_raw = load_data(symbol, timeframe, use_live)
    state = run_agent(
        symbol=symbol,
        timeframe=timeframe,
        candles=candles,
        news=news_raw,
        use_live=use_live,
    )
    return state


def run_analysis_no_openai(symbol: str, timeframe: str, use_live: bool):
    """Chạy pipeline đơn giản (không dùng OpenAI)."""
    from src.api.schemas import MarketData, OHLCV, NewsItem
    from src.agents.technical_analyst import TechnicalAnalystAgent
    from src.agents.sentiment_analyzer import SentimentAnalyzerAgent
    from src.agents.signal_generator import SignalGeneratorAgent

    candles, news_raw = load_data(symbol, timeframe, use_live)
    ohlcv = [OHLCV(**c) for c in candles]
    md = MarketData(symbol=symbol, timeframe=timeframe,
                    current_price=ohlcv[-1].close, candles=ohlcv)
    news_items = [NewsItem(title=n["title"], source=n.get("source",""),
                           content=n.get("content", n["title"]),
                           published_at=n.get("published_at","")) for n in news_raw]
    tech = TechnicalAnalystAgent().analyze_technical(md)
    sent = SentimentAnalyzerAgent().analyze_sentiment(news_items)
    sig  = SignalGeneratorAgent().generate_signals(symbol=symbol, sentiment=sent, technical=tech)
    return md, tech, sent, sig, news_raw


def run_openai_analysis(
    symbol, timeframe, md, tech, sent, sig, news_raw
) -> dict | None:
    """Gọi OpenAI để phân tích chính sách tổng hợp."""
    try:
        from src.agents.openai_analyst import OpenAIAnalystAgent
        agent = OpenAIAnalystAgent()

        tech_dict = {
            "trend": tech.trend,
            "rsi": tech.rsi,
            "macd": tech.macd,
            "moving_averages": {
                "ma_20": tech.moving_averages.ma_20,
                "ma_50": tech.moving_averages.ma_50,
                "ma_200": tech.moving_averages.ma_200,
                "cross_signal": tech.moving_averages.cross_signal,
            },
            "key_levels": tech.key_levels,
        }
        sent_dict = {
            "label": sent.label.value if hasattr(sent.label, "value") else str(sent.label),
            "score": sent.score,
            "reasoning": sent.reasoning,
        }
        sig_dict = {
            "action": sig.action.value,
            "confidence": sig.confidence,
            "entry_zone": sig.entry_zone,
            "stop_loss": sig.stop_loss,
            "take_profit": sig.take_profit,
            "reasoning": sig.reasoning,
        }
        return agent.analyze(
            symbol=symbol,
            timeframe=timeframe,
            current_price=md.current_price,
            technical=tech_dict,
            sentiment=sent_dict,
            signal=sig_dict,
            news=news_raw,
        )
    except Exception as e:
        console.print(f"[yellow]⚠ OpenAI error: {e}[/yellow]")
        return None

# ── Graph Result Display ──────────────────────────────────────────────────────

def display_graph_result(state: dict, symbol: str, timeframe: str, mode: str):
    """Hiển thị kết quả được xác nhận bởi LangGraph Consensus Engine."""
    action   = state["final_action"]
    conf     = state["final_confidence"]
    warning  = state["warning"]
    retry    = state["retry_count"]
    color    = _signal_color(action)

    # Badge đồng thuận
    consensus = state.get("consensus", False)
    badge = (
        f"[bold green]\u2705 ĐỒNG THUẬN[/bold green]"
        if consensus
        else f"[bold red]\u26a0\ufe0f KHÔNG ĐỒNG THUẬN ({retry} lần thử)[/bold red]"
    )

    now = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    console.print(Rule(f"[bold cyan]\u26a1 AGENTIC AI TRADING[/bold cyan]  [dim]{now}[/dim]  [yellow]{mode}[/yellow]"))

    # === FINAL SIGNAL ===
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    t.add_column(style="dim", width=22)
    t.add_column()
    t.add_row("Cặp giao dịch",  f"[bold white]{symbol}[/bold white]  [{color}]{timeframe}[/{color}]")
    t.add_row("Giá hiện tại",   f"[bold white]{fmt(state['md'].current_price)}[/bold white] USDT")
    t.add_row("Kết luận Graph",  badge)
    t.add_row("Tín hiệu cuối",  f"[bold {color}]{action}[/bold {color}]")
    t.add_row("Độ tự tin",      _conf_bar(conf))
    if state["final_entry_zone"]:
        ez = state["final_entry_zone"]
        t.add_row("Entry Zone", f"[cyan]{fmt(ez[0])}[/cyan] \u2013 [cyan]{fmt(ez[1])}[/cyan]")
    t.add_row("Stop Loss",
        f"[red]{fmt(state['final_stop_loss'])}[/red]" if state["final_stop_loss"] else "[dim]N/A[/dim]")
    t.add_row("Take Profit",
        f"[green]{fmt(state['final_take_profit'])}[/green]" if state["final_take_profit"] else "[dim]N/A[/dim]")

    if state["final_stop_loss"] and state["final_take_profit"] and state["final_entry_zone"]:
        ez = state["final_entry_zone"]
        entry = (ez[0] + ez[1]) / 2
        risk   = abs(entry - state["final_stop_loss"])
        reward = abs(state["final_take_profit"] - entry)
        rr = reward / risk if risk > 0 else 0
        rr_c = "green" if rr >= 1.5 else "yellow"
        t.add_row("R:R Ratio", f"[{rr_c}]1 : {rr:.2f}[/{rr_c}]")

    if state["final_key_levels"]:
        t.add_row("Mức giá chính",
                  "  ".join(f"[white]{l}[/white]" for l in state["final_key_levels"]))

    panel_color = color if consensus else "red"
    console.print(Panel(t,
        title=f"[bold {panel_color}] 🤖 KẾT QUẢ CONSENSUS ENGINE [/bold {panel_color}]",
        border_style=panel_color))

    # === Technical + Sentiment ===
    display_result(state["md"], state["tech"], state["sent"],
                   state["signal"], state["news"], symbol, timeframe, mode)

    # === AI Reasoning ===
    console.print(Panel(
        f"[white]{state['final_reasoning']}[/white]",
        title="[bold cyan]💬 Consensus Reasoning[/bold cyan]",
        border_style="cyan"
    ))

    # === Warning ===
    if warning:
        console.print(Panel(
            f"[bold red]{warning}[/bold red]",
            title="[bold red]⚠️ Cảnh Báo[/bold red]",
            border_style="red"
        ))


def display_result(md, tech, sent, sig, news_raw, symbol, timeframe, mode):
    clear()
    now = datetime.now().strftime("%H:%M:%S %d/%m/%Y")

    # === Header ===
    console.print(Rule(f"[bold cyan]⚡ AGENTIC AI TRADING[/bold cyan]  [dim]{now}[/dim]  [yellow]{mode}[/yellow]"))

    # === Signal Panel ===
    action = sig.action.value
    color = _signal_color(action)
    action_text = f"[bold {color}]{action}[/bold {color}]"

    signal_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    signal_table.add_column(style="dim", width=18)
    signal_table.add_column()
    signal_table.add_row("Cặp giao dịch",  f"[bold white]{symbol}[/bold white]  [{color}]{timeframe}[/{color}]")
    signal_table.add_row("Giá hiện tại",   f"[bold white]{fmt(md.current_price)}[/bold white] USDT")
    signal_table.add_row("Tín hiệu AI",    action_text)
    signal_table.add_row("Độ tự tin",      _conf_bar(sig.confidence))
    if sig.entry_zone:
        signal_table.add_row("Entry Zone",
            f"[cyan]{fmt(sig.entry_zone[0])}[/cyan] – [cyan]{fmt(sig.entry_zone[1])}[/cyan]")
    signal_table.add_row("Stop Loss",
        f"[red]{fmt(sig.stop_loss)}[/red]" if sig.stop_loss else "[dim]N/A[/dim]")
    signal_table.add_row("Take Profit",
        f"[green]{fmt(sig.take_profit)}[/green]" if sig.take_profit else "[dim]N/A[/dim]")

    # R:R ratio
    if sig.stop_loss and sig.take_profit and sig.entry_zone:
        entry = (sig.entry_zone[0] + sig.entry_zone[1]) / 2
        risk = abs(entry - sig.stop_loss)
        reward = abs(sig.take_profit - entry)
        rr = reward / risk if risk > 0 else 0
        rr_color = "green" if rr >= 1.5 else "yellow"
        signal_table.add_row("R:R Ratio", f"[{rr_color}]1 : {rr:.2f}[/{rr_color}]")

    console.print(Panel(signal_table,
        title=f"[bold {color}] 🎯 TÍN HIỆU GIAO DỊCH [/bold {color}]",
        border_style=color))

    # === Technical Indicators ===
    tech_table = Table(title="📊 Chỉ Số Kỹ Thuật", box=box.ROUNDED,
                       border_style="blue", show_lines=True)
    tech_table.add_column("Chỉ số", style="dim", width=18)
    tech_table.add_column("Giá trị", justify="right", width=16)
    tech_table.add_column("Tín hiệu", width=20)

    trend_c = _trend_color(tech.trend)
    tech_table.add_row("Xu hướng", f"[{trend_c}]{tech.trend}[/{trend_c}]", "")
    tech_table.add_row("RSI (14)", f"[white]{tech.rsi:.2f}[/white]", _rsi_label(tech.rsi))

    macd_c = "green" if tech.macd > 0 else "red"
    tech_table.add_row("MACD", f"[{macd_c}]{tech.macd:.4f}[/{macd_c}]",
                        f"[{macd_c}]{'Bullish' if tech.macd > 0 else 'Bearish'}[/{macd_c}]")

    ma = tech.moving_averages
    cross_c = "green" if ma.cross_signal == "Golden Cross" else "red" if ma.cross_signal == "Death Cross" else "white"
    tech_table.add_row("MA 20", fmt(ma.ma_20), "")
    tech_table.add_row("MA 50", fmt(ma.ma_50), "")
    tech_table.add_row("MA 200", fmt(ma.ma_200), "")
    tech_table.add_row("MA Cross", f"[{cross_c}]{ma.cross_signal}[/{cross_c}]", "")
    tech_table.add_row("Support",    f"[green]{fmt(tech.key_levels.get('support'))}[/green]", "[dim]Vùng hỗ trợ[/dim]")
    tech_table.add_row("Resistance", f"[red]{fmt(tech.key_levels.get('resistance'))}[/red]", "[dim]Vùng kháng cự[/dim]")

    # === Sentiment ===
    sent_label = sent.label.value if hasattr(sent.label, "value") else str(sent.label)
    sent_c = _trend_color(sent_label)
    sent_table = Table(title="🧠 Tâm Lý Thị Trường", box=box.ROUNDED,
                       border_style="magenta", show_lines=True)
    sent_table.add_column("Mục", style="dim", width=12)
    sent_table.add_column("Giá trị")

    sent_table.add_row("Nhãn",    f"[bold {sent_c}]{sent_label}[/bold {sent_c}]")
    sent_table.add_row("Điểm",    f"[white]{sent.score:.2f}[/white]  (−1.0 → +1.0)")
    sent_table.add_row("Lý do",   f"[dim]{sent.reasoning}[/dim]")
    if sent.keywords:
        sent_table.add_row("Keywords", "[cyan]" + "  ".join(sent.keywords[:6]) + "[/cyan]")

    console.print(Columns([tech_table, sent_table], equal=False, expand=False))

    # === Reasoning ===
    console.print(Panel(
        f"[dim]{sig.reasoning}[/dim]",
        title="[bold]💬 Lý Luận AI[/bold]", border_style="dim"
    ))

    # === News ===
    if news_raw:
        news_table = Table(title="📰 Tin Tức", box=box.SIMPLE, border_style="dim")
        news_table.add_column("#", style="dim", width=3)
        news_table.add_column("Tiêu đề", width=60)
        news_table.add_column("Nguồn", style="cyan", width=16)
        for i, n in enumerate(news_raw[:5], 1):
            news_table.add_row(str(i), n["title"][:60], n.get("source", "")[:16])
        console.print(news_table)


def display_openai_panel(ai: dict, original_action: str, original_conf: float):
    """Hiển thị panel phân tích GPT-4o."""
    if not ai:
        return

    confirmed = ai.get("confirmed_action", original_action)
    conf_adj  = float(ai.get("confidence_adjustment", 0.0))
    new_conf  = max(0.0, min(1.0, original_conf + conf_adj))
    bias      = ai.get("overall_bias", "NEUTRAL")
    warning   = ai.get("warning")

    c_action = _signal_color(confirmed)
    c_bias   = _trend_color(bias)

    ai_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    ai_table.add_column(style="dim", width=22)
    ai_table.add_column()

    ai_table.add_row("Bias tổng quát",
                     f"[bold {c_bias}]{bias}[/bold {c_bias}]")
    ai_table.add_row("Hành động xác nhận",
                     f"[bold {c_action}]{confirmed}[/bold {c_action}]")
    adj_sign = "+" if conf_adj >= 0 else ""
    ai_table.add_row("Độ tự tin điều chỉnh",
                     f"{_conf_bar(new_conf)}  ([dim]{adj_sign}{conf_adj*100:.1f}% GPT[/dim])")

    entry  = ai.get("entry_advice", "")
    risk   = ai.get("risk_advice", "")
    ctx    = ai.get("market_context", "")
    detail = ai.get("detailed_reasoning", "")
    levels = ai.get("key_levels", [])

    if entry:  ai_table.add_row("Lời khuyẫn entry",  f"[cyan]{entry}[/cyan]")
    if risk:   ai_table.add_row("Quản lý rủi ro",   f"[yellow]{risk}[/yellow]")
    if ctx:    ai_table.add_row("Bối cảnh TT",      f"[dim]{ctx}[/dim]")
    if levels: ai_table.add_row("Mức giá quan trọng", "  ".join(f"[white]{l}[/white]" for l in levels))

    panel_color = "bright_green" if confirmed == "BUY" else "bright_red" if confirmed == "SELL" else "bright_yellow"
    console.print(Panel(ai_table,
        title=f"[bold {panel_color}] 🤖 GPT-4o ANALYSIS [/bold {panel_color}]",
        border_style=panel_color))

    if detail:
        console.print(Panel(
            f"[white]{detail}[/white]",
            title="[bold cyan]💬 GPT-4o Phân Tích Chi Tiết[/bold cyan]",
            border_style="cyan"
        ))

    if warning:
        console.print(Panel(
            f"[bold red]{warning}[/bold red]",
            title="[bold red]⚠️ Cảnh Báo[/bold red]",
            border_style="red"
        ))

# ── Menu Functions ────────────────────────────────────────────────────────────

def select_symbol() -> str:
    console.print("\n[bold]Chọn cặp giao dịch:[/bold]")
    table = Table(box=box.SIMPLE, show_header=False)
    table.add_column("No.", style="cyan", width=4)
    table.add_column("Symbol", width=12)
    table.add_column("No.", style="cyan", width=4)
    table.add_column("Symbol", width=12)
    for i in range(0, len(SYMBOLS), 2):
        row = [str(i+1), SYMBOLS[i]]
        if i+1 < len(SYMBOLS):
            row += [str(i+2), SYMBOLS[i+1]]
        else:
            row += ["", ""]
        table.add_row(*row)
    console.print(table)
    while True:
        choice = Prompt.ask("[cyan]Nhập số (1-10)[/cyan]", default="1")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(SYMBOLS):
                return SYMBOLS[idx]
        except ValueError:
            # Allow direct input like "BTC/USDT"
            upper = choice.upper()
            if "/" in upper:
                return upper
        console.print("[red]Lựa chọn không hợp lệ, thử lại.[/red]")

def select_timeframe() -> str:
    console.print("\n[bold]Chọn khung thời gian:[/bold]")
    table = Table(box=box.SIMPLE, show_header=False)
    table.add_column("Phím", style="cyan", width=6)
    table.add_column("Khung", width=10)
    table.add_column("Mô tả", style="dim")
    for k, (tf, desc) in TIMEFRAMES.items():
        table.add_row(f"[{k}]", tf, desc)
    console.print(table)
    choice = Prompt.ask("[cyan]Chọn[/cyan]", choices=list(TIMEFRAMES.keys()), default="4")
    return TIMEFRAMES[choice][0]

def select_interval() -> int:
    console.print("\n[bold]Tự động phân tích theo chu kỳ:[/bold]")
    table = Table(box=box.SIMPLE, show_header=False)
    table.add_column("Phím", style="cyan", width=6)
    table.add_column("Chu kỳ", style="white")
    for k, (sec, desc) in INTERVALS.items():
        table.add_row(f"[{k}]", desc)
    console.print(table)
    choice = Prompt.ask("[cyan]Chọn[/cyan]", choices=list(INTERVALS.keys()), default="2")
    return INTERVALS[choice][0]

def select_openai() -> bool:
    has_key = bool(os.getenv("OPENAI_KEY") or os.getenv("OPENAI_API_KEY"))
    if not has_key:
        console.print("[dim](Không tìm thấy OPENAI_KEY trong .env — bỏ qua GPT-4o)[/dim]")
        return False
    console.print("\n[bold]Dùng GPT-4o để xác nhận & đào sâu tín hiệu?[/bold]")
    console.print("  [1] [green]Có[/green]  — Gọi OpenAI GPT-4o (tốn ~1-2 giây)")
    console.print("  [2] [dim]Không[/dim] — Chỉ dùng phân tích kỹ thuật")
    choice = Prompt.ask("[cyan]Chọn[/cyan]", choices=["1", "2"], default="1")
    return choice == "1"

def select_mode() -> bool:
    console.print("\n[bold]Chế độ dữ liệu:[/bold]")
    console.print("  [1] [green]Demo[/green]  — Dữ liệu giả lập (không cần API)")
    console.print("  [2] [red]Live[/red]   — Dữ liệu thực từ Binance Futures")
    choice = Prompt.ask("[cyan]Chọn[/cyan]", choices=["1", "2"], default="2")
    return choice == "2"

# ── Main CLI Loop ─────────────────────────────────────────────────────────────

def main():
    clear()
    banner()

    # Setup signal handler để thoát sạch bằng Ctrl+C
    running = {"ok": True}
    def _exit(sig, frame):
        running["ok"] = False
        console.print("\n\n[yellow]⏹ Đã dừng. Tạm biệt![/yellow]\n")
        sys.exit(0)
    signal.signal(signal.SIGINT, _exit)

    console.print()

    # === Cấu hình ban đầu ===
    symbol    = select_symbol()
    timeframe = select_timeframe()
    interval  = select_interval()
    use_live  = select_mode()

    has_openai = bool(os.getenv("OPENAI_KEY") or os.getenv("OPENAI_API_KEY"))
    use_openai = select_openai() if has_openai else False
    mode_label = f"{'\ud83d\udd34 LIVE' if use_live else '\ud83d\udfe1 DEMO'}{'  \ud83e\udd16 Consensus' if use_openai else ''}"

    console.print(f"\n[bold green]✓ Cấu hình:[/bold green]  "
                  f"[white]{symbol}[/white] / [cyan]{timeframe}[/cyan] / "
                  f"{'Auto ' + str(interval) + 's' if interval else 'Một lần'} / {mode_label}")
    console.print("[dim]Nhấn Ctrl+C bất kỳ lúc nào để dừng và quay về menu.[/dim]\n")

    cycle = 0
    while running["ok"]:
        cycle += 1

        # Chạy phân tích với spinner
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task(
                f"🧠 Đang phân tích {symbol} ({timeframe}) lần #{cycle}...", total=None)
            try:
                if use_openai:
                    # LangGraph Consensus Engine
                    state = run_analysis(symbol, timeframe, use_live)
                else:
                    # Phân tích kỹ thuật đơn giản
                    md, tech, sent, sig, news_raw = run_analysis_no_openai(symbol, timeframe, use_live)
            except Exception as e:
                console.print(f"\n[red]❌ Lỗi phân tích: {e}[/red]")
                import traceback; traceback.print_exc()
                time.sleep(5)
                continue

        if use_openai:
            display_graph_result(state, symbol, timeframe, mode_label)
        else:
            display_result(md, tech, sent, sig, news_raw, symbol, timeframe, mode_label)

        # Chỉ chạy 1 lần
        if interval == 0:
            console.print("\n[dim]Nhấn Enter để phân tích lại, hoặc Ctrl+C để thoát.[/dim]")
            try:
                input()
            except (EOFError, KeyboardInterrupt):
                break
            continue

        # Đếm ngược đến lần tiếp theo
        console.print(f"\n[dim]Lần tiếp theo sau [cyan]{interval}[/cyan] giây... (Ctrl+C để dừng)[/dim]")
        try:
            for remaining in range(interval, 0, -1):
                if not running["ok"]:
                    break
                bar = "▓" * int((interval - remaining) / interval * 30) + "░" * int(remaining / interval * 30)
                console.print(
                    f"  [{bar}] [cyan]{remaining:3d}s[/cyan]",
                    end="\r"
                )
                time.sleep(1)
            console.print()  # newline
        except KeyboardInterrupt:
            break

        # Hỏi có muốn đổi cấu hình không
        if running["ok"]:
            try:
                change = Confirm.ask("\n[yellow]Đổi cấu hình trước khi phân tích tiếp?[/yellow]", default=False)
                if change:
                    clear()
                    banner()
                    symbol    = select_symbol()
                    timeframe = select_timeframe()
                    interval  = select_interval()
                    use_live  = select_mode()
                    has_openai = bool(os.getenv("OPENAI_KEY") or os.getenv("OPENAI_API_KEY"))
                    use_openai = select_openai() if has_openai else False
                    mode_label = f"{'\ud83d\udd34 LIVE' if use_live else '\ud83d\udfe1 DEMO'}{'  \ud83e\udd16 Consensus' if use_openai else ''}"
                    cycle = 0
            except (EOFError, KeyboardInterrupt):
                break

    console.print("\n[green]✓ Tạm biệt![/green]\n")

if __name__ == "__main__":
    main()
