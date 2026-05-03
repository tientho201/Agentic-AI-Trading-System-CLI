from src.logging.logger import logger
from src.exception.exception import CustomException
import sys
from src.api.schemas import MarketData, TechnicalResult, MovingAverages
import pandas as pd
import pandas_ta as ta


class TechnicalAnalystAgent:
    def __init__(self):
        pass
        
    def analyze_technical(self, market_data: MarketData) -> TechnicalResult:
        """
        Phân tích dữ liệu thị trường và trả về kết quả phân tích kỹ thuật.
        """
        logger.info(f"Analyzing technical data for {market_data.symbol} on {market_data.timeframe}")
        try:
            # Create a list of dictionaries instead of list of tuples
            df = pd.DataFrame([
                {
                    'timestamp': candle.timestamp,
                    'open': candle.open,
                    'high': candle.high,
                    'low': candle.low,
                    'close': candle.close,
                    'volume': candle.volume
                }
                for candle in market_data.candles
            ])
            df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Đảm bảo dữ liệu sắp xếp theo thời gian (từ cũ đến mới)
            df = df.sort_values(by='timestamp') 
            
            # Calculate Moving Averages
            df.ta.sma(length=20, append=True)
            df.ta.sma(length=50, append=True)
            df.ta.sma(length=200, append=True)
            df.ta.rsi(length=14, append=True)
            df.ta.macd(fast=12, slow=26, signal=9, append=True)
            
            # Get the latest moving averages
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            
            ma_20 = latest.get('SMA_20', 0.0)
            if pd.isna(ma_20): ma_20 = 0.0
            
            ma_50 = latest.get('SMA_50', 0.0)
            if pd.isna(ma_50): ma_50 = 0.0
            
            ma_200 = latest.get('SMA_200', 0.0)
            if pd.isna(ma_200): ma_200 = 0.0
            
            rsi = latest.get('RSI_14', 50.0)
            if pd.isna(rsi): rsi = 50.0
            
            # MACD often gen 3 cloumns: MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
            macd_line = latest.get('MACD_12_26_9', 0.0)
            if pd.isna(macd_line): macd_line = 0.0
            
            macd_signal_line = latest.get('MACDs_12_26_9', 0.0)
            if pd.isna(macd_signal_line): macd_signal_line = 0.0
            
            # Determine MACD Signal
            macd_signal = "NEUTRAL"
            if macd_line > macd_signal_line:
                macd_signal = "BULLISH" # Đường MACD cắt lên Signal 
            elif macd_line < macd_signal_line:
                macd_signal = "BEARISH" # Đường MACD cắt xuống Signal
            
            # Determine Trend
            cross_signal = "NEUTRAL"
            
            prev_ma_50 = prev.get("SMA_50", 0.0)
            if pd.isna(prev_ma_50): prev_ma_50 = 0.0
            
            prev_ma_200 = prev.get("SMA_200", 0.0)
            if pd.isna(prev_ma_200): prev_ma_200 = 0.0
            
            if prev_ma_50 <= prev_ma_200 and ma_50 > ma_200 and ma_50 != 0.0 and ma_200 != 0.0:
                cross_signal = "Golden Cross" # Giao cắt vàng, tín hiệu Tăng
            elif prev_ma_50 >= prev_ma_200 and ma_50 < ma_200 and ma_50 != 0.0 and ma_200 != 0.0:
                cross_signal = "Death Cross" # Giao cắt tử, tín hiệu Giảm
                
            trend = "NEUTRAL"
            if cross_signal == "Golden Cross" or macd_signal == "BULLISH":
                trend = "BULLISH"
            elif cross_signal == "Death Cross" or macd_signal == "BEARISH":
                trend = "BEARISH"
        
            logger.info(f"Technical analysis completed for {market_data.symbol}")  
            return TechnicalResult(
                rsi=rsi,
                macd=macd_line,
                trend=trend,
                key_levels={"support": df['low'].min(), "resistance": df['high'].max()},
                moving_averages=MovingAverages(
                    ma_20=ma_20,
                    ma_50=ma_50,
                    ma_200=ma_200,
                    cross_signal=cross_signal
                )
            )
        except Exception as e:
            logger.error(f"Error analyzing market data: {e}")
            raise CustomException(e, sys)