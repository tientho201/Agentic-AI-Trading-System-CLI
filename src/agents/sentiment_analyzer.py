import pandas as pd
import pandas_ta as ta
from src.api.schemas import MarketData, TechnicalResult, MovingAverages , NewsItem, SetimentResults
from src.logging.logger import logger
from src.exception.exception import CustomException
import sys
from typing import List, Optional

class SentimentAnalyzerAgent:
    def __init__(self):
        self.bullish_words = [
            'surge', 'jump', 'soar', 'adopt', 'approve', 'positive', 
            'bull', 'high', 'partnership', 'launch', 'breakout', 'growth'
        ]
        
        # Tập từ khóa mang cảm xúc Tiêu cực (Bearish)
        self.bearish_words = [
            'crash', 'drop', 'ban', 'hack', 'negative', 'bear', 
            'low', 'fear', 'lawsuit', 'scam', 'plunge', 'sell-off'
        ]
    
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
        
    def analyze_sentiment(self, news_list: List[NewsItem]) -> SetimentResults:
        """
        Đọc danh sách tin tức, chấm điểm cảm xúc và đưa ra kết luận.
        Điểm chạy từ -1.0 (Cực kỳ bi quan) đến 1.0 (Cực kỳ lạc quan).
        """
        logger.info(f"Analyzing sentiment for {news_list}")
        try:
            if not news_list:
                logger.warning("No news data available")
                return SetimentResults(
                    score=0.0,
                    label="NEUTRAL", 
                    reasoning="Không có dữ liệu tin tức.",
                    keywords=[]
                )
            total_score = 0.0 
            analyzed_news = 0
            
            for news in news_list:
                text_to_analyze = f"{news.title} {news.content}".lower()
             
                bullish_score = sum(text_to_analyze.count(word) for word in self.bullish_words)
                bullish_word = [word for word in self.bullish_words if word in text_to_analyze.lower()]
                
                bearish_score = sum(text_to_analyze.count(word) for word in self.bearish_words)
                bearish_word = [word for word in self.bearish_words if word in text_to_analyze.lower()]
                
                if bullish_score > bearish_score:
                    article_score = 0.5 + (0.1 * bullish_score) 
                elif bearish_score > bullish_score:
                    article_score = -0.5 - (0.1 * bearish_score)
                else:
                    article_score = 0.0 
                
                # Cắt viền điểm số không cho vượt quá -1.0 và 1.0
                article_score = max(-1.0, min(1.0, article_score))
                
                total_score += article_score
                analyzed_news += 1
                
            # Tính điểm trung bình của toàn bộ tin tức
            average_score = total_score / analyzed_news

            # Xác định label dựa trên điểm số trung bình
            if average_score > 0.3:
                sentiment_label = "BULLISH"
                keywords = bullish_word
            elif average_score < -0.3:
                sentiment_label = "BEARISH"
                keywords = bearish_word
            else:
                sentiment_label = "NEUTRAL"
                keywords = []
                
            # Tạo một câu tóm tắt để báo cáo
            reasoning = f"Dựa trên {analyzed_news} bài báo, tâm lý chung đang là {sentiment_label} với điểm số {average_score:.2f}."
            return SetimentResults(
                score=average_score,
                label=sentiment_label,
                reasoning=reasoning,
                keywords=keywords
            )   
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            raise CustomException(e, sys)