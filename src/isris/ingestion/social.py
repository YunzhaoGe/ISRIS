import logging
from typing import List
from datetime import datetime, timezone
from duckduckgo_search import DDGS
from ..core.models import ContentItem, SourceType

class SocialInvestigator:
    """中文社交舆情调查员：专门搜寻雪球、股吧、知乎等平台的讨论"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def search_chinese_sentiment(self, ticker: str, company_name: str = None) -> List[ContentItem]:
        """
        搜寻 A 股社交媒体上的散户情绪和热门讨论。
        """
        results = []
        name = company_name or ticker
        
        # 针对 A 股的社交平台定向搜索
        queries = [
            f"{name} site:xueqiu.com",           # 雪球深度讨论
            f"{name} site:guba.eastmoney.com",  # 股吧散户情绪
            f"{name} site:zhihu.com 评价"         # 知乎中长篇分析
        ]

        self.logger.info(f"💬  Scanning Chinese social sentiment for {name}...")
        
        try:
            with DDGS() as ddgs:
                for query in queries:
                    search_results = ddgs.text(query, max_results=5)
                    for r in search_results:
                        results.append(ContentItem(
                            id=r.get('href'),
                            title=f"[SOCIAL] {r.get('title', '')}",
                            content=r.get('body', ''),
                            url=r.get('href'),
                            source_type=SourceType.NEWS, # 暂用 NEWS，但在标题标注了 [SOCIAL]
                            author="Social Media",
                            publish_time=datetime.now(timezone.utc)
                        ))
        except Exception as e:
            self.logger.error(f"❌ Social sentiment search failed: {e}")
            
        return results
