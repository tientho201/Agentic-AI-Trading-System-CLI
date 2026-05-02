from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

# ===== Enums =====
# Sentiment labels for sentiment analysis
class SetimentLabel(str , Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class TradeAction(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

# # Liquidation Data
# class LiquidationLevels(BaseModel):
#     price_level: float = Field(description="Price level where liquidation occurs")
#     volume: float = Field(description="Estimated liquidation volume (USD)")

# class LiquidationData(BaseModel):
#     long_levels: List[LiquidationLevels] = Field(description="Long liquidation levels")
#     short_levels: List[LiquidationLevels] = Field(description="Short liquidation levels")
#     major_cluster: str = Field(description="Description of the largest liquidation cluster (e.g., 'Short positions are heavily concentrated around the $65,000 region')")

# ===== Data Models =====
class OHLCV(BaseModel):
    """Open-High-Low-Close-Volume data point"""
    timestamp: int = Field(description="Candle closing time (Unix timestamp)")
    open: float = Field(description="Opening price")
    high: float = Field(description="Highest price")
    low: float = Field(description="Lowest price")
    close: float = Field(description="Closing price")
    volume: float = Field(description="Trading volume")

class MarketData(BaseModel):
    """Market data snapshot with historical OHLCV data"""
    symbol: str = Field(description="Trading symbol (e.g. BTC/USD)")
    timeframe: str = Field(description="Candle timeframe (e.g. '1h', '1d')")
    current_price: float = Field(description="Current value of the asset")
    candles: List[OHLCV] = Field(description="List of historical candle data")
    # liquidation_data: Optional[LiquidationData] = Field(default=None, description="Liquidation data from api Coinglass/Binance")

class NewsItem(BaseModel):
    """News item schema"""
    title: str = Field(description="New title of Article")
    source: str = Field(description="Source of the news")
    content: str = Field(description="Content of the news")
    published_at: str = Field(description="Timestamp of the news")
    url: Optional[str] = Field(default=None, description="URL of the news")

class SentimentAnalysis(BaseModel):
    """Sentiment analysis result for a given text"""
    label: SetimentLabel = Field(description="Sentiment label (positive, negative, neutral)")
    score: float = Field(description="Confidence score (0.0 to 1.0)")
    reasoning: str = Field(description="Reasoning behind the sentiment analysis")
    keywords: List[str] = Field(description="Keywords extracted from the text")
    
# Agent Result
class MovingAverages(BaseModel):
    ma_20: float = Field(description="20-period Simple Moving Average")
    ma_50: float = Field(description="50-period Simple Moving Average")
    ma_200: float = Field(description="200-period Simple Moving Average")
    cross_signal: str = Field(description="Golden Cross or Death Cross signal")

class TechnicalResult(BaseModel):
    """Technical Analysis Agent Result"""
    rsi: float = Field(description="Relative Strength Index (RSI)")
    macd: float = Field(description="Moving Average Convergence Divergence (MACD)")
    trend: str = Field(description="Current trend (bullish, bearish, neutral)")
    key_levels: dict = Field(description="Important support and resistance zones", example={"support": 60000, "resistance": 65000})
    moving_averages: MovingAverages = Field(description="Moving averages analysis")
   
class SetimentResults(BaseModel):
    """Sentiment analysis result for a given text"""
    label: SetimentLabel = Field(description="Sentiment label (positive, negative, neutral)")
    score: float = Field(description="Confidence score (0.0 to 1.0)")
    reasoning: str = Field(description="Reasoning behind the sentiment analysis")
    keywords: List[str] = Field(description="Keywords extracted from the text")

# Final Output
class TradingSignal(BaseModel):
    """Final Trading Signal"""
    symbol: str = Field(description="Trading symbol (e.g. BTC/USD)")
    action: TradeAction = Field(description="Trading action (buy, sell, hold)")
    confidence: float = Field(description="Confidence score (0.0 to 1.0)")
    entry_zone: Optional[List[float]] = Field(description="Ideal price range to enter the trade", default=None)
    stop_loss: Optional[float] = Field(description="Stop-loss price", default=None)
    take_profit: Optional[float] = Field(description="Take-profit price", default=None)
    reasoning: str = Field(description="Reasoning behind the trading signal")
    timestamp: datetime = Field(description="Timestamp of the trading signal", default_factory=datetime.utcnow )
    