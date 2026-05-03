from src.logging.logger import logger
from src.exception.exception import CustomException
import sys
from typing import Union, List, Optional
from src.api.schemas import SetimentResults, TechnicalResult, TradingSignal, TradeAction
from datetime import datetime

class SignalGeneratorAgent:
    def __init__(self):
        pass
    
    def generate_signals(self, symbol: str, sentiment: SetimentResults, technical: TechnicalResult) -> TradingSignal:
        """
        Generate trading signals based on sentiment and technical analysis.
        """
        logger.info(f"Generating signals for {symbol}")
        try:
            action = self._determine_signal(sentiment, technical)
            
            signal = TradingSignal(
                symbol=symbol,
                action=action,
                confidence=self._calculate_confidence(sentiment, technical),
                reasoning=self._generate_reasoning(sentiment, technical, action),
                timestamp=datetime.utcnow(),
                entry_zone=self._calculate_entry_zone(technical, action),
                stop_loss=self._calculate_stop_loss(technical, action),
                take_profit=self._calculate_take_profit(technical, action)
            )
            logger.info(f"Signal generated for {symbol}: {action.value}")
            return signal
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            raise CustomException(e, sys)

    def _determine_signal(self, sentiment: SetimentResults, technical: TechnicalResult) -> TradeAction:
        tech_trend = technical.trend
        sent_label = sentiment.label
        rsi = technical.rsi
        
        if tech_trend == "BULLISH" and sent_label in ["BULLISH", "NEUTRAL"]:
            if rsi < 70:
                return TradeAction.BUY
        elif tech_trend == "BEARISH" and sent_label in ["BEARISH", "NEUTRAL"]:
            if rsi > 30:
                return TradeAction.SELL
                
        if rsi < 30 and tech_trend == "BULLISH":
            return TradeAction.BUY
        if rsi > 70 and tech_trend == "BEARISH":
            return TradeAction.SELL
            
        if sent_label == "BULLISH" and sentiment.score > 0.7 and tech_trend != "BEARISH":
            return TradeAction.BUY
        if sent_label == "BEARISH" and sentiment.score < -0.7 and tech_trend != "BULLISH":
            return TradeAction.SELL
            
        return TradeAction.HOLD

    def _calculate_confidence(self, sentiment: SetimentResults, technical: TechnicalResult) -> float:
        confidence = 0.0
        
        sent_strength = abs(sentiment.score)
        confidence += sent_strength * 0.4
        
        tech_score = 0.0
        if technical.trend != "NEUTRAL":
            tech_score += 0.3
            
        if technical.moving_averages.cross_signal != "NEUTRAL":
            tech_score += 0.2
            
        if 40 <= technical.rsi <= 60:
            tech_score += 0.1
        elif technical.rsi < 30 or technical.rsi > 70:
            tech_score += 0.1
            
        confidence += tech_score
        
        return min(1.0, round(confidence, 2))

    def _generate_reasoning(self, sentiment: SetimentResults, technical: TechnicalResult, action: TradeAction) -> str:
        reasoning = f"Signal: {action.value}. "
        reasoning += f"Technical Analysis indicates {technical.trend} trend (RSI: {technical.rsi:.2f}, MACD: {technical.macd:.4f}, Cross: {technical.moving_averages.cross_signal}). "
        reasoning += f"Sentiment Analysis is {sentiment.label} with score {sentiment.score:.2f}. "
        
        if action == TradeAction.BUY:
            reasoning += "Confluence suggests an upward movement."
        elif action == TradeAction.SELL:
            reasoning += "Confluence suggests a downward movement."
        else:
            reasoning += "Lack of strong confluence or conflicting signals suggest holding."
            
        return reasoning

    def _calculate_entry_zone(self, technical: TechnicalResult, action: TradeAction) -> Optional[List[float]]:
        support = technical.key_levels.get("support", 0)
        resistance = technical.key_levels.get("resistance", 0)
        
        if action == TradeAction.BUY:
            return [round(support, 2), round(support * 1.02, 2)]
        elif action == TradeAction.SELL:
            return [round(resistance * 0.98, 2), round(resistance, 2)]
        return None

    def _calculate_stop_loss(self, technical: TechnicalResult, action: TradeAction) -> Optional[float]:
        support = technical.key_levels.get("support", 0)
        resistance = technical.key_levels.get("resistance", 0)
        
        if action == TradeAction.BUY:
            return round(support * 0.98, 2)
        elif action == TradeAction.SELL:
            return round(resistance * 1.02, 2)
        return None

    def _calculate_take_profit(self, technical: TechnicalResult, action: TradeAction) -> Optional[float]:
        support = technical.key_levels.get("support", 0)
        resistance = technical.key_levels.get("resistance", 0)
        
        if action == TradeAction.BUY:
            return round(resistance * 0.98, 2)
        elif action == TradeAction.SELL:
            return round(support * 1.02, 2)
        return None