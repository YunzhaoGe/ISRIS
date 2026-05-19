import logging
from typing import List
from datetime import datetime, timezone
from duckduckgo_search import DDGS
from ..core.models import ContentItem, SourceType

class SocialInvestigator:
    """中文社交舆情调查员：专门搜寻雪球、股吧等平台的讨论"""

    def __init__(self):
        self.logger = logging.getLogger("isris.ingestion.social")

    async def search_chinese_sentiment(self, ticker: str, company_name: str = None) -> List[ContentItem]:
        name = company_name or ticker
        queries = [
            f"{name} site:xueqiu.com",
            f"{name} site:guba.eastmoney.com"
        ]

        self.logger.info(f"💬 Scanning Chinese social sentiment for {name}...")
        results = []
        
        try:
            with DDGS() as ddgs:
                for query in queries:
                    try:
                        search_results = list(ddgs.text(query, max_results=5))
                        for r in search_results:
                            results.append(ContentItem(
                                id=r.get('href'),
                                title=f"[SOCIAL] {r.get('title', '')}",
                                content=r.get('body', ''),
                                url=r.get('href'),
                                source_type=SourceType.NEWS,
                                author="Social Media",
                                publish_time=datetime.now(timezone.utc)
                            ))
                    except Exception:
                        continue
        except Exception as e:
            self.logger.error(f"❌ Social search failed: {e}")
            
        return results
