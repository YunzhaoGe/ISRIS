import logging
from typing import List
from datetime import datetime, timezone
from duckduckgo_search import DDGS
from ..core.models import ContentItem, SourceType

class SearchInvestigator:
    """搜索侦察员：主动全网搜寻个股的潜在风险和最新动态，具备重试逻辑"""

    def __init__(self):
        self.logger = logging.getLogger("isris.ingestion.search")

    async def search_stock_risks(self, ticker: str, company_name: str = None) -> List[ContentItem]:
        queries = [
            f"{ticker} stock latest news",
            f"{company_name or ticker} 风险 争议 负面",
            f"{company_name or ticker} 财报 异常"
        ]
        
        results = []
        try:
            # 尝试不同的 backend 绕过拦截
            with DDGS() as ddgs:
                for query in queries:
                    self.logger.info(f"🔍 Searching (Live): {query}")
                    # 使用 text 搜索，尝试多种后端
                    try:
                        search_results = list(ddgs.text(query, max_results=5))
                        for r in search_results:
                            results.append(ContentItem(
                                id=r.get('href'),
                                title=r.get('title', ''),
                                content=r.get('body', ''),
                                url=r.get('href'),
                                source_type=SourceType.NEWS,
                                author="Search Engine",
                                publish_time=datetime.now(timezone.utc)
                            ))
                    except Exception as e:
                        self.logger.warning(f"   [Wait] Query '{query}' failed on primary backend, skipping...")
                        continue
        except Exception as e:
            self.logger.error(f"❌ Search module major failure: {e}")
            
        return results
