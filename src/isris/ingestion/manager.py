import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

import httpx
try:
    import yfinance as yf
except ImportError:
    yf = None

from isris.core.models import ContentItem, SourceType, MarketQuote
from isris.ingestion.search import SearchInvestigator

class IngestionManager:
    """数据摄取管理器：协调不同来源的抓取器"""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.search_investigator = SearchInvestigator()

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
        获取与股票相关的实时新闻（并行：RSS + 主动搜索）。
        """
        ticker = self._normalize_ticker(stock_identifier)
        self.logger.info(f"🛰️  Ingesting multi-source intelligence for {ticker}...")
        
        # 1. 启动并行任务
        rss_task = self._fetch_rss_news(ticker)
        search_task = self.search_investigator.search_stock_risks(ticker)
        
        results = await asyncio.gather(rss_task, search_task, return_exceptions=True)
        
        all_items = []
        for res in results:
            if isinstance(res, list):
                all_items.extend(res)
            elif isinstance(res, Exception):
                self.logger.error(f"Ingestion task failed: {res}")

        # 2. 语义去重 (未来可接入 Horizon 的 SimHash)
        # 简单根据 URL 去重
        unique_items = {item.url: item for item in all_items}.values()
        
        self.logger.info(f"✅ Ingestion complete: {len(unique_items)} unique signals found.")
        return list(unique_items)

    async def _fetch_rss_news(self, ticker: str) -> List[ContentItem]:
        """抓取 RSS 财经新闻"""
        items = []
        rss_url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(rss_url, timeout=10.0)
                if response.status_code == 200:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(response.content)
                    for channel in root.findall("channel"):
                        for item in channel.findall("item")[:10]:
                            title = item.find("title").text
                            link = item.find("link").text
                            items.append(ContentItem(
                                id=link,
                                title=title,
                                content=title,
                                url=link,
                                source_type=SourceType.NEWS,
                                publish_time=datetime.now(timezone.utc)
                            ))
            except Exception as e:
                self.logger.warning(f"RSS fetch failed for {ticker}: {e}")
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
