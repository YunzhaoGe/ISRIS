import logging
from typing import List
from datetime import datetime, timezone
from duckduckgo_search import DDGS
from ..core.models import ContentItem, SourceType

class SearchInvestigator:
    """搜索侦察员：主动全网搜寻个股的潜在风险和最新动态"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def search_stock_risks(self, ticker: str, company_name: str = None) -> List[ContentItem]:
        """
        根据代码和名称搜索相关风险信息。
        """
        # 构建搜索词：1. 基础新闻 2. 风险与争议
        queries = [
            f"{ticker} stock latest news",
            f"{company_name or ticker} 风险 争议 负面",
            f"{company_name or ticker} 财报 异常"
        ]
        
        results = []
        try:
            with DDGS() as ddgs:
                for query in queries:
                    self.logger.info(f"🔍 Active Searching: {query}")
                    # 获取最近的新闻/网页结果
                    search_results = ddgs.text(query, max_results=5)
                    
                    for r in search_results:
                        results.append(ContentItem(
                            id=r.get('href'),
                            title=r.get('title', ''),
                            content=r.get('body', ''), # 搜索结果的摘要
                            url=r.get('href'),
                            source_type=SourceType.NEWS,
                            author="DuckDuckGo Search",
                            publish_time=datetime.now(timezone.utc) # 搜索结果通常不带精确时间，暂设为现在
                        ))
        except Exception as e:
            self.logger.error(f"❌ Search enhancement failed: {e}")
            
        return results
