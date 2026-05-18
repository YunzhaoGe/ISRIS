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

    def _normalize_ticker(self, ticker: str) -> str:
        """
        标准化股票代码，自动处理 A 股和港股后缀。
        """
        ticker = ticker.upper().strip()
        # 处理 6 位数字代码 (A 股)
        if len(ticker) == 6 and ticker.isdigit():
            if ticker.startswith(('6', '9')): # 沪市
                return f"{ticker}.SS"
            else: # 深市或北交所
                return f"{ticker}.SZ"
        # 处理 4 位或 5 位数字代码 (港股)
        if (len(ticker) == 4 or len(ticker) == 5) and ticker.isdigit():
            return f"{ticker.zfill(5)}.HK"
        return ticker

    async def fetch_stock_news(self, stock_identifier: str, days: int = 30) -> List[ContentItem]:
        """
        获取与股票相关的实时新闻和社交媒体讨论。
        """
        ticker = self._normalize_ticker(stock_identifier)
        self.logger.info(f"Fetching real news for {ticker} via RSS...")
        
        items = []
        # 使用 Yahoo Finance 的 RSS 作为示例源
        rss_url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
        
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
        获取市场行情数据和基础财务信息。使用 asyncio.to_thread 防止阻塞。
        """
        ticker_symbol = self._normalize_ticker(stock_identifier)
        if not yf:
            self.logger.warning("yfinance not installed, returning empty market data")
            return {}

        self.logger.info(f"Fetching market data for {ticker_symbol}")
        
        def _get_data():
            ticker = yf.Ticker(ticker_symbol)
            # history 和 info 都是同步网络调用
            hist = ticker.history(period="5d")
            if not hist.empty:
                hist.index = hist.index.strftime('%Y-%m-%d')
            return {
                "info": ticker.info,
                "history": hist
            }

        try:
            # 在独立线程中运行同步调用
            data = await asyncio.to_thread(_get_data)
            info = data["info"]
            hist = data["history"]
            
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
