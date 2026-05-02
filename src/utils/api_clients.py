
import feedparser
from binance.client import Client

from src.logging.logger import logger
from src.exception.exception import CustomException

import os
import sys

from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())

class FreeNewsDay:
    def __init__(self):
        self.base_url = "https://news.google.com/rss/search?q={query}+crypto&hl=en-US&gl=US&ceid=US:en"


    def get_recent_news(self, symbol: str, limit: int = 5 ) -> list:
        """
        Get recent news from Google News
        
        Args:
            symbol (str): Trading symbol (e.g. BTC/USD)
            limit (int): Maximum number of news articles to retrieve
        
        Returns:
            list: List of news articles in dictionary format
        """
        logger.info(f"Fetching recent news for {symbol}")
        # clean text (Example: BTC/USDT -> BTC)
        clean_symbol = symbol.split("/")[0].lower() if "/" in symbol else symbol.lower()

        # build url
        url = self.base_url.format(query=clean_symbol)

        try:
            feed = feedparser.parse(url)
            articles = []
            
            for entry in feed.entries[:limit]:
                articles.append({
                    "title": entry.title,
                    "source": entry.source,
                    "content": entry.summary.split('target="_blank"')[1].split("</a>&nbsp;&nbsp;")[0][1:],
                    "published_at": entry.published,
                    "url": entry.link
                })

            return articles

        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            raise CustomException(e, sys)
        
class BinanceClient:
    def __init__(self):
        self.client = Client(api_key=os.getenv("BINANCE_API_KEY"), api_secret=os.getenv("BINANCE_API_SECRET"))
        
    def get_OHCLV(self, symbol: str = "BTC/USDT", timeframe: str = "1h", limit: int = 500) -> list:
        try:
            logger.info(f"Fetching OHLCV for {symbol}")
            # clean symbol if contains "/"  
            if "/"  in symbol:
                clean_symbol = symbol.replace('/', '').upper()
            else:
                clean_symbol = symbol.upper()
            # Hàm của python-binance trả về sẵn list dữ liệu nến
            klines = self.client.futures_klines(symbol=clean_symbol, interval=timeframe, limit=limit)
    
            # Chỉ việc format lại theo schema của mình
            return [{
                "timestamp": k[0],
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5])
            } for k in klines]
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            raise CustomException(e, sys)

if __name__ == "__main__":
    binance_client = BinanceClient()
    print(binance_client.get_OHCLV())