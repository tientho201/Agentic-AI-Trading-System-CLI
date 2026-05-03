"""
OpenAI Trading Analyst Agent
Dùng GPT-4o để phân tích thị trường chuyên sâu dựa trên dữ liệu kỹ thuật + sentiment.
"""
import os
import json
from dotenv import load_dotenv, find_dotenv
from src.logging.logger import logger

load_dotenv(find_dotenv())


class OpenAIAnalystAgent:
    """
    Agent dùng GPT-4o để đưa ra phân tích tổng hợp, lý luận giao dịch
    và xác nhận / bác bỏ tín hiệu từ các agent kỹ thuật.
    """

    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        api_key = os.getenv("OPENAI_KEY") or os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("Không tìm thấy OPENAI_KEY trong .env")
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)

    def analyze(
        self,
        symbol: str,
        timeframe: str,
        current_price: float,
        technical: dict,
        sentiment: dict,
        signal: dict,
        news: list,
    ) -> dict:
        """
        Gửi toàn bộ dữ liệu thị trường cho GPT-4o và nhận phân tích chuyên sâu.

        Returns:
            dict với các keys:
              - overall_bias: "BULLISH" | "BEARISH" | "NEUTRAL"
              - confidence_adjustment: float (-0.2 đến +0.2) — điều chỉnh confidence từ agent kỹ thuật
              - confirmed_action: "BUY" | "SELL" | "HOLD"
              - entry_advice: str — lời khuyên cụ thể về entry
              - risk_advice: str — quản lý rủi ro
              - key_levels: list[str] — các mức giá quan trọng cần theo dõi
              - market_context: str — bối cảnh thị trường tổng thể
              - detailed_reasoning: str — phân tích đầy đủ
              - warning: str | None — cảnh báo đặc biệt nếu có
        """
        try:
            prompt = self._build_prompt(
                symbol, timeframe, current_price,
                technical, sentiment, signal, news
            )
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Bạn là một chuyên gia phân tích thị trường crypto với hơn 10 năm kinh nghiệm. "
                            "Bạn được cung cấp dữ liệu kỹ thuật và tâm lý thị trường từ hệ thống AI. "
                            "Nhiệm vụ: phân tích tổng hợp và đưa ra lời khuyên giao dịch chính xác, thực tế. "
                            "Luôn trả lời bằng JSON hợp lệ theo đúng schema được yêu cầu. "
                            "Ngôn ngữ phân tích: Tiếng Việt."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=1500,
            )

            raw = response.choices[0].message.content
            result = json.loads(raw)
            logger.info(f"OpenAI analysis: {symbol} → {result.get('confirmed_action')}")
            return result

        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return {
                "overall_bias": sentiment.get("label", "NEUTRAL"),
                "confidence_adjustment": 0.0,
                "confirmed_action": signal.get("action", "HOLD"),
                "entry_advice": "Không thể kết nối OpenAI, dùng tín hiệu gốc.",
                "risk_advice": "Quản lý rủi ro theo tín hiệu kỹ thuật.",
                "key_levels": [],
                "market_context": "OpenAI không khả dụng.",
                "detailed_reasoning": str(e),
                "warning": f"⚠ OpenAI error: {e}"
            }

    def _build_prompt(self, symbol, timeframe, price, tech, sent, sig, news) -> str:
        ma = tech.get("moving_averages", {})
        kl = tech.get("key_levels", {})
        news_text = "\n".join([f"- {n.get('title','')}" for n in (news or [])[:5]])

        entry_zone = sig.get("entry_zone")
        entry_str = (
            f"{entry_zone[0]:.4f} – {entry_zone[1]:.4f}" if entry_zone else "N/A"
        )

        return f"""
Phân tích thị trường cho: {symbol} | Khung thời gian: {timeframe}

=== DỮ LIỆU THỊ TRƯỜNG ===
Giá hiện tại: {price:.4f} USDT

--- Chỉ số kỹ thuật ---
Xu hướng:     {tech.get('trend', 'N/A')}
RSI (14):     {tech.get('rsi', 0):.2f}
MACD:         {tech.get('macd', 0):.4f}
MA 20:        {ma.get('ma_20', 0):.4f}
MA 50:        {ma.get('ma_50', 0):.4f}
MA 200:       {ma.get('ma_200', 0):.4f}
MA Cross:     {ma.get('cross_signal', 'N/A')}
Support:      {kl.get('support', 0):.4f}
Resistance:   {kl.get('resistance', 0):.4f}

--- Tâm lý thị trường ---
Nhãn:         {sent.get('label', 'N/A')}
Điểm:         {sent.get('score', 0):.2f}
Lý do:        {sent.get('reasoning', '')}

--- Tín hiệu từ hệ thống AI ---
Hành động:    {sig.get('action', 'N/A')}
Độ tự tin:    {sig.get('confidence', 0) * 100:.1f}%
Entry Zone:   {entry_str}
Stop Loss:    {sig.get('stop_loss', 'N/A')}
Take Profit:  {sig.get('take_profit', 'N/A')}
Lý luận gốc: {sig.get('reasoning', '')}

--- Tin tức mới nhất ---
{news_text if news_text else 'Không có tin tức'}

=== YÊU CẦU ===
Hãy phân tích toàn diện và trả về JSON với schema SAU (không thêm key khác):

{{
  "overall_bias": "BULLISH" | "BEARISH" | "NEUTRAL",
  "confidence_adjustment": <số thực từ -0.2 đến +0.2 — tăng/giảm confidence so với hệ thống>,
  "confirmed_action": "BUY" | "SELL" | "HOLD",
  "entry_advice": "<lời khuyên cụ thể về điểm vào, nếu nên vào lệnh>",
  "risk_advice": "<quản lý rủi ro: % vốn, SL cụ thể, trailing stop nếu cần>",
  "key_levels": ["<mức giá 1>", "<mức giá 2>", "..."],
  "market_context": "<bối cảnh thị trường tổng thể trong 1-2 câu>",
  "detailed_reasoning": "<phân tích chi tiết 3-5 câu, đề cập RSI, MACD, MA, support/resistance>",
  "warning": "<cảnh báo đặc biệt hoặc null nếu không có>"
}}
"""
