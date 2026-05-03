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