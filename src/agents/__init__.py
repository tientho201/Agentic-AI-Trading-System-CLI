"""
All agent in system
- Data Gatherer Agent : gather data from api
- Technical Analyst Agent : analyze technical indicators
- News Analyzer Agent : analyze news
- Sentiment Analyzer Agent : analyze sentiment
- Decision Maker Agent : make decision

Bộ chỉ báo kỹ thuật bạn đề cập (MACD 12,26,9, RSI 14, SMA 20/50/200) tạo nên một hệ thống phân tích toàn diện, kết hợp giữa động lượng (momentum) và xu hướng (trend). 

Dưới đây là cách phối hợp các chỉ báo này trong phân tích kỹ thuật:
1. Phân Tích Xu Hướng (Trend) - Bộ 3 SMA
SMA 200 (Dài hạn): Xác định xu hướng chính. Giá > SMA200 là xu hướng tăng (uptrend), Giá < SMA200 là giảm (downtrend).
SMA 50 (Trung hạn): Xác định xu hướng trung hạn và đóng vai trò hỗ trợ/kháng cự động.
SMA 20 (Ngắn hạn): Xác định xu hướng ngắn hạn và các điểm vào lệnh nhanh.
Tín hiệu: Crossover (Giao cắt) - SMA 50 cắt lên SMA 200 (Golden Cross) là tín hiệu tăng mạnh. 

2. Phân Tích Động Lượng (Momentum) - RSI (14)
RSI (14) > 50: Động lượng tăng (bullish).
RSI (14) < 50: Động lượng giảm (bearish).
Quá mua (Overbought) > 70: Cân nhắc chốt lời.
Quá bán (Oversold) < 30: Cân nhắc tìm điểm mua. 

3. Phân Tích Xu Hướng & Tín Hiệu - MACD (12, 26, 9)
MACD Line > Signal Line: Tín hiệu tăng (mua), cột histogram dương.
MACD Line < Signal Line: Tín hiệu giảm (bán), cột histogram âm.
Cắt trên/dưới đường 0: Thể hiện sự chuyển đổi xu hướng dài hạn hơn. 

4. Kết Hợp Chiến Lược Giao Dịch
Tín hiệu 	Điều kiện kết hợp
Mua (Long)	1. Giá nằm trên SMA 200 & SMA 50.
2. MACD cắt lên đường Signal và > 0.
3. RSI > 50 (và đang hướng lên).
Bán (Short)	1. Giá nằm dưới SMA 200 & SMA 50.
2. MACD cắt xuống đường Signal và < 0.
3. RSI < 50 (và đang hướng xuống).
Lưu ý: Bạn nên sử dụng các chỉ báo này trên cùng khung thời gian để có tín hiệu đồng nhất, thường dùng SMA 200/50 trên đồ thị ngày (Daily) để xác định xu hướng chính và MACD/RSI trên đồ thị ngắn hơn để tìm điểm vào. 

Ba chỉ báo này bổ sung cho nhau rất tốt: Đường Trung Bình Động cho bạn thấy hướng đi lớn của giá, trong khi RSI và MACD cảnh báo thời điểm giá có thể đảo chiều hoặc tiếp tục đà.

# 5. Phân Tích Cảm Tính (Sentiment Analysis)
Thu thập và phân tích tin tức (News), thông báo trên mạng xã hội (Social Media) để đánh giá mức độ tích cực (Bullish) hay tiêu cực (Bearish) của thị trường.

Tác dụng: Giúp phát hiện các yếu tố bất ngờ (tin tức đột xuất, tin đồn) ảnh hưởng đến giá.

Chỉ báo kết hợp:

- Sentiment Score: Tính điểm số dựa trên tần suất xuất hiện các từ khóa Bullish/Bearish trong tin tức.
"""