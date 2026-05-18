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
        self.logger.info(f"Fetching real news for {stock_identifier} via RSS...")
        
        items = []
        # 使用 Yahoo Finance 的 RSS 作为示例源
        rss_url = f"https://finance.yahoo.com/rss/headline?s={stock_identifier}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(rss_url, timeout=10.0)
                if response.status_code == 200:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(response.content)
                    for channel in root.findall("channel"):
                        for item in channel.findall("item")[:10]: # 限制 10 条
                            title = item.find("title").text
                            link = item.find("link").text
                            pub_date_str = item.find("pubDate").text
                            # 简单转换时间，生产环境建议用 dateutil
                            items.append(ContentItem(
                                id=link,
                                title=title,
                                content=title, # RSS 通常只给标题
                                url=link,
                                source_type=SourceType.NEWS,
                                publish_time=datetime.now(timezone.utc) # 简化处理
                            ))
            except Exception as e:
                self.logger.error(f"Error fetching RSS news: {e}")

        # 如果 RSS 失败，返回一个保底的占位符
        if not items:
            items.append(ContentItem(
                id="manual-1",
                title=f"Monitoring {stock_identifier} for major events",
                content="System is scanning for news updates...",
                url=f"https://finance.yahoo.com/quote/{stock_identifier}",
                source_type=SourceType.NEWS,
                publish_time=datetime.now(timezone.utc)
            ))
            
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
            
            # 关键修复：将 Timestamp 索引转换为字符串，否则 json.dumps 会报错
            if not hist.empty:
                hist.index = hist.index.strftime('%Y-%m-%d')
            
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
