import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

import httpx
try:
    import yfinance as yf
except ImportError:
    yf = None

from ..core.models import ContentItem, SourceType, MarketQuote

class IngestionManager:
    """数据摄取管理器：协调不同来源的抓取器"""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

    async def fetch_stock_news(self, stock_identifier: str, days: int = 30) -> List[ContentItem]:
        """
        获取与股票相关的实时新闻和社交媒体讨论。
        """
        # TODO: 这里应该集成真正的 Horizon Scrapers
        # 目前返回更高质量的 Mock 数据模拟抓取结果
        items = [
            ContentItem(
                id=f"news-{i}",
                title=f"{stock_identifier} Update: Market sentiment remains volatile",
                content="Analysts are closely watching the upcoming earnings call...",
                url=f"https://finance.yahoo.com/quote/{stock_identifier}",
                source_type=SourceType.NEWS,
                publish_time=datetime.now(timezone.utc) - timedelta(hours=i*5)
            ) for i in range(3)
        ]
        return items

    async def fetch_market_data(self, stock_identifier: str) -> Dict[str, Any]:
        """
        获取市场行情数据和基础财务信息。
        """
        if not yf:
            self.logger.warning("yfinance not installed, returning empty market data")
            return {}

        self.logger.info(f"Fetching market data for {stock_identifier}")
        try:
            # yfinance 的调用通常是阻塞的，在大规模系统中应放在 thread pool 中执行
            ticker = yf.Ticker(stock_identifier)
            
            # 获取最近 5 天的行情
            hist = ticker.history(period="5d")
            
            # 获取公司基本信息
            info = ticker.info
            
            return {
                "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "currency": info.get("currency"),
                "market_cap": info.get("marketCap"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "recent_history": hist.to_dict() if not hist.empty else {}
            }
        except Exception as e:
            self.logger.error(f"Error fetching market data from yfinance: {e}")
            return {}
