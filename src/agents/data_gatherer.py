from src.api.schemas import MarketData, OHLCV , NewsItem
from src.utils.api_clients import BinanceClient, FreeNewsDay

from src.logging.logger import logger
from src.exception.exception import CustomException
import sys
from typing import List
from datetime import datetime

class DataGathererAgent:
    def __init__(self):
        self.binance_client = BinanceClient()
        self.news_api = FreeNewsDay()

    def gather_data(self, symbol: str , timeframe: str, limit: int = 100) -> MarketData:
        """
        Gather market data from various sources
        
        Args:
            symbol (str): Trading symbol (e.g. BTC/USD)
            timeframe (str): Timeframe for candle data (e.g. "1h", "1d")
            limit (int): Maximum number of news articles to retrieve
        
        Returns:
            MarketData: Market data
        """ 
        logger.info(f"Gathering data for {symbol}")
        try:
            raw_candles =  self.binance_client.get_OHCLV(symbol=symbol, timeframe=timeframe, limit=limit)
            
            candles = [OHLCV(**candle) for candle in raw_candles]
            current_price = candles[-1].close if candles else 0.0
            logger.info(f"Market data gathered for {symbol}")
            return MarketData(
                symbol=symbol,
                timeframe=timeframe,
                current_price=current_price,
                candles=candles
            )   
        except CustomException as e:
            logger.error(f"Error gathering data for {symbol}: {e}")
            raise CustomException(e, sys)
    
    
    def gather_news(self, symbol: str , limit: int = 10) -> List[NewsItem]:
        """
        Gather news data from various sources
        
        Args:
            symbol (str): Trading symbol (e.g. BTC/USD)
            limit (int): Maximum number of news articles to retrieve
        
        Returns:
            List[NewsItem]: List of news articles
        """ 
        logger.info(f"Gathering news for {symbol}")
        try:
            raw_news =  self.news_api.get_recent_news(symbol=symbol, limit=limit)
            logger.info(f"News data gathered for {symbol}")
            return raw_news
        except CustomException as e:
            logger.error(f"Error gathering news for {symbol}: {e}")
            raise CustomException(e, sys)