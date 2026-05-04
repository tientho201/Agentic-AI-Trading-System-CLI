"""
Trading Agent Graph — LangGraph Consensus Engine
=================================================
Luồng:
  load_data → technical_analysis → signal_generation
                                        ↓
                                  openai_analysis
                                        ↓
                                  consensus_check ──── MATCH ──→ finalize
                                        │
                                   NO MATCH
                                        │
                                retry_count < MAX? ──YES──→ retry_openai → consensus_check
                                        │
                                        NO
                                        ↓
                                  force_finalize (warning)

Quy tắc đồng thuận (consensus):
  - BUY  ↔ BUY   → MATCH
  - SELL ↔ SELL  → MATCH
  - HOLD ↔ HOLD  → MATCH
  - BUY  ↔ HOLD  → NO MATCH (neutral disagreement — retry)
  - BUY  ↔ SELL  → NO MATCH (hard conflict — retry × 2)
  - SELL ↔ HOLD  → NO MATCH (neutral disagreement — retry)
"""
from __future__ import annotations

import os
from typing import Any, TypedDict

from dotenv import load_dotenv, find_dotenv
from langgraph.graph import StateGraph, END

from src.logging.logger import logger

load_dotenv(find_dotenv())

MAX_RETRIES = 3


# ── State ─────────────────────────────────────────────────────────────────────

class TradingState(TypedDict):
    # Input
    symbol: str
    timeframe: str
    use_live: bool
    candles: list
    news: list

    # Intermediate
    md: Any                   # MarketData object
    tech: Any                 # TechnicalResult object
    sent: Any                 # SentimentResult object
    signal: Any               # SignalResult object  (from signal_generator)
    openai_result: dict       # dict (from openai_analyst)

    # Consensus tracking
    retry_count: int
    consensus: bool           # True nếu 2 agent đồng thuận

    # Final output
    final_action: str         # BUY | SELL | HOLD
    final_confidence: float
    final_reasoning: str
    final_entry_zone: list | None
    final_stop_loss: float | None
    final_take_profit: float | None
    final_key_levels: list
    warning: str | None


# ── Node: Load Data ───────────────────────────────────────────────────────────

def node_load_data(state: TradingState) -> TradingState:
    """Đã được chuẩn bị từ CLI (candles + news đã có trong state)."""
    logger.info(f"[Graph] load_data: {state['symbol']} | {len(state['candles'])} candles")
    return state


# ── Node: Technical Analysis ──────────────────────────────────────────────────

def node_technical_analysis(state: TradingState) -> TradingState:
    from src.api.schemas import MarketData, OHLCV, NewsItem
    from src.agents.technical_analyst import TechnicalAnalystAgent
    from src.agents.sentiment_analyzer import SentimentAnalyzerAgent

    logger.info(f"[Graph] technical_analysis: {state['symbol']}")

    ohlcv = [OHLCV(**c) for c in state["candles"]]
    md = MarketData(
        symbol=state["symbol"],
        timeframe=state["timeframe"],
        current_price=ohlcv[-1].close,
        candles=ohlcv,
    )

    news_items = [
        NewsItem(
            title=n["title"],
            source=n.get("source", ""),
            content=n.get("content", n["title"]),
            published_at=n.get("published_at", ""),
        )
        for n in state["news"]
    ]

    tech = TechnicalAnalystAgent().analyze_technical(md)
    sent = SentimentAnalyzerAgent().analyze_sentiment(news_items)

    return {**state, "md": md, "tech": tech, "sent": sent}


# ── Node: Signal Generation ───────────────────────────────────────────────────

def node_signal_generation(state: TradingState) -> TradingState:
    from src.agents.signal_generator import SignalGeneratorAgent

    logger.info(f"[Graph] signal_generation: {state['symbol']}")
    sig = SignalGeneratorAgent().generate_signals(
        symbol=state["symbol"],
        sentiment=state["sent"],
        technical=state["tech"],
    )
    logger.info(f"[Graph] Technical signal → {sig.action.value} ({sig.confidence:.0%})")
    return {**state, "signal": sig}


# ── Node: OpenAI Analysis ─────────────────────────────────────────────────────

def node_openai_analysis(state: TradingState) -> TradingState:
    from src.agents.openai_analyst import OpenAIAnalystAgent

    logger.info(f"[Graph] openai_analysis: {state['symbol']} (retry={state['retry_count']})")

    tech = state["tech"]
    sent = state["sent"]
    sig  = state["signal"]

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

    openai_result = OpenAIAnalystAgent().analyze(
        symbol=state["symbol"],
        timeframe=state["timeframe"],
        current_price=state["md"].current_price,
        technical=tech_dict,
        sentiment=sent_dict,
        signal=sig_dict,
        news=state["news"],
    )
    logger.info(f"[Graph] OpenAI signal → {openai_result.get('confirmed_action')} "
                f"(adj={openai_result.get('confidence_adjustment', 0):+.0%})")
    return {**state, "openai_result": openai_result}


# ── Node: Retry OpenAI (with disagreement context) ───────────────────────────

def node_retry_openai(state: TradingState) -> TradingState:
    """
    Khi 2 agent bất đồng, gọi lại OpenAI với context bổ sung:
    'Technical agent nói X nhưng OpenAI trước đó nói Y — hãy cân nhắc lại.'
    """
    from src.agents.openai_analyst import OpenAIAnalystAgent

    tech_action   = state["signal"].action.value
    openai_action = state["openai_result"].get("confirmed_action", "HOLD")
    retry         = state["retry_count"]

    logger.info(
        f"[Graph] retry_openai #{retry}: conflict {tech_action} vs {openai_action}"
    )

    # Bơm thêm context bất đồng vào news để OpenAI biết
    conflict_note = {
        "title": (
            f"[SYSTEM RETRY #{retry}] Conflict detected: Technical analysis says '{tech_action}' "
            f"but AI previously said '{openai_action}'. Re-evaluate carefully with all evidence."
        ),
        "source": "ConsensusEngine",
        "published_at": "now",
        "content": (
            f"Iteration {retry}. Technical Agent → {tech_action}. "
            f"OpenAI previous → {openai_action}. "
            "Please provide a definitive signal with stronger justification."
        ),
    }
    augmented_news = [conflict_note] + state["news"][:4]

    tech = state["tech"]
    sent = state["sent"]
    sig  = state["signal"]

    openai_result = OpenAIAnalystAgent().analyze(
        symbol=state["symbol"],
        timeframe=state["timeframe"],
        current_price=state["md"].current_price,
        technical={
            "trend": tech.trend, "rsi": tech.rsi, "macd": tech.macd,
            "moving_averages": {
                "ma_20": tech.moving_averages.ma_20,
                "ma_50": tech.moving_averages.ma_50,
                "ma_200": tech.moving_averages.ma_200,
                "cross_signal": tech.moving_averages.cross_signal,
            },
            "key_levels": tech.key_levels,
        },
        sentiment={
            "label": sent.label.value if hasattr(sent.label, "value") else str(sent.label),
            "score": sent.score,
            "reasoning": sent.reasoning,
        },
        signal={
            "action": sig.action.value,
            "confidence": sig.confidence,
            "entry_zone": sig.entry_zone,
            "stop_loss": sig.stop_loss,
            "take_profit": sig.take_profit,
            "reasoning": sig.reasoning,
        },
        news=augmented_news,
    )

    new_retry = state["retry_count"] + 1
    logger.info(
        f"[Graph] retry_openai result → {openai_result.get('confirmed_action')} "
        f"(attempt {new_retry}/{MAX_RETRIES})"
    )
    return {**state, "openai_result": openai_result, "retry_count": new_retry}


# ── Node: Consensus Check ─────────────────────────────────────────────────────

def node_consensus_check(state: TradingState) -> TradingState:
    tech_action   = state["signal"].action.value
    openai_action = state["openai_result"].get("confirmed_action", "HOLD")
    consensus     = tech_action == openai_action

    logger.info(
        f"[Graph] consensus_check: tech={tech_action}, openai={openai_action} "
        f"→ {'✅ MATCH' if consensus else '❌ MISMATCH'}"
    )
    return {**state, "consensus": consensus}


# ── Node: Finalize (MATCH) ────────────────────────────────────────────────────

def node_finalize(state: TradingState) -> TradingState:
    sig = state["signal"]
    oai = state["openai_result"]

    # Confidence được tăng thêm khi 2 agent đồng thuận
    adj    = float(oai.get("confidence_adjustment", 0.0))
    conf   = min(1.0, sig.confidence + abs(adj) + 0.05)   # bonus +5% khi match
    action = sig.action.value

    logger.info(
        f"[Graph] finalize (CONSENSUS): {action} | conf={conf:.0%} "
        f"| retries={state['retry_count']}"
    )

    return {
        **state,
        "final_action": action,
        "final_confidence": conf,
        "final_reasoning": (
            f"[✅ ĐỒNG THUẬN sau {state['retry_count']} lần kiểm tra]\n"
            f"Technical: {sig.reasoning}\n"
            f"GPT-4o: {oai.get('detailed_reasoning', '')}"
        ),
        "final_entry_zone":  sig.entry_zone,
        "final_stop_loss":   sig.stop_loss,
        "final_take_profit": sig.take_profit,
        "final_key_levels":  oai.get("key_levels", []),
        "warning": oai.get("warning"),
    }


# ── Node: Force Finalize (NO CONSENSUS after max retries) ────────────────────

def node_force_finalize(state: TradingState) -> TradingState:
    sig        = state["signal"]
    oai        = state["openai_result"]
    tech_action = sig.action.value
    oai_action  = oai.get("confirmed_action", "HOLD")

    # Khi conflict: mặc định an toàn hơn là HOLD
    # Nếu 1 trong 2 là HOLD → dùng HOLD
    # Nếu BUY vs SELL (hard conflict) → HOLD bắt buộc
    if "HOLD" in (tech_action, oai_action):
        final_action = "HOLD"
    elif tech_action != oai_action:   # BUY vs SELL
        final_action = "HOLD"
    else:
        final_action = tech_action

    # Confidence giảm khi không đồng thuận
    conf = max(0.1, sig.confidence * 0.6)

    logger.warning(
        f"[Graph] force_finalize (NO CONSENSUS): tech={tech_action}, "
        f"openai={oai_action} → fallback={final_action} | conf={conf:.0%}"
    )

    warning = (
        f"⚠️ Không đồng thuận sau {MAX_RETRIES} lần: "
        f"Technical={tech_action}, GPT-4o={oai_action}. "
        f"Tín hiệu '{final_action}' được đưa ra với độ tự tin THẤP. "
        "Hãy cân nhắc kỹ trước khi vào lệnh!"
    )

    return {
        **state,
        "final_action":     final_action,
        "final_confidence": conf,
        "final_reasoning": (
            f"[❌ KHÔNG ĐỒNG THUẬN — fallback an toàn]\n"
            f"Technical Agent: {sig.reasoning}\n"
            f"GPT-4o: {oai.get('detailed_reasoning', '')}"
        ),
        "final_entry_zone":  None,
        "final_stop_loss":   None,
        "final_take_profit": None,
        "final_key_levels":  oai.get("key_levels", []),
        "warning": warning,
    }


# ── Conditional Edge: after consensus_check ──────────────────────────────────

def edge_after_consensus(state: TradingState) -> str:
    if state["consensus"]:
        return "finalize"
    if state["retry_count"] < MAX_RETRIES:
        return "retry_openai"
    return "force_finalize"


# ── Build Graph ───────────────────────────────────────────────────────────────

def build_trading_graph() -> StateGraph:
    g = StateGraph(TradingState)

    # Nodes
    g.add_node("load_data",          node_load_data)
    g.add_node("technical_analysis", node_technical_analysis)
    g.add_node("signal_generation",  node_signal_generation)
    g.add_node("openai_analysis",    node_openai_analysis)
    g.add_node("consensus_check",    node_consensus_check)
    g.add_node("retry_openai",       node_retry_openai)
    g.add_node("finalize",           node_finalize)
    g.add_node("force_finalize",     node_force_finalize)

    # Edges (linear flow)
    g.add_edge("load_data",          "technical_analysis")
    g.add_edge("technical_analysis", "signal_generation")
    g.add_edge("signal_generation",  "openai_analysis")
    g.add_edge("openai_analysis",    "consensus_check")

    # Conditional: consensus_check → finalize | retry | force_finalize
    g.add_conditional_edges(
        "consensus_check",
        edge_after_consensus,
        {
            "finalize":       "finalize",
            "retry_openai":   "retry_openai",
            "force_finalize": "force_finalize",
        },
    )

    # retry_openai → back to consensus_check
    g.add_edge("retry_openai",   "consensus_check")

    # Terminals
    g.add_edge("finalize",       END)
    g.add_edge("force_finalize", END)

    g.set_entry_point("load_data")
    return g.compile()


# ── Public API ────────────────────────────────────────────────────────────────

_GRAPH = None

def get_graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_trading_graph()
    return _GRAPH


def run_agent(
    symbol: str,
    timeframe: str,
    candles: list,
    news: list,
    use_live: bool = False,
) -> TradingState:
    """
    Entry point chính — gọi từ CLI.

    Args:
        symbol:    vd "BTC/USDT"
        timeframe: vd "1h"
        candles:   list[dict] với keys timestamp/open/high/low/close/volume
        news:      list[dict] với keys title/source/published_at
        use_live:  bool

    Returns:
        TradingState đầy đủ với kết quả final_action, final_confidence, ...
    """
    initial_state: TradingState = {
        "symbol":        symbol,
        "timeframe":     timeframe,
        "use_live":      use_live,
        "candles":       candles,
        "news":          news,
        # Sẽ được điền bởi nodes
        "md":            None,
        "tech":          None,
        "sent":          None,
        "signal":        None,
        "openai_result": {},
        # Tracking
        "retry_count":   0,
        "consensus":     False,
        # Output
        "final_action":     "",
        "final_confidence": 0.0,
        "final_reasoning":  "",
        "final_entry_zone": None,
        "final_stop_loss":  None,
        "final_take_profit": None,
        "final_key_levels": [],
        "warning":          None,
    }

    graph   = get_graph()
    result  = graph.invoke(initial_state)
    return result