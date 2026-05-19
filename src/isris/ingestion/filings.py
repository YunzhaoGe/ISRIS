import logging
from typing import List
from datetime import datetime, timezone
from duckduckgo_search import DDGS
from ..core.models import ContentItem, SourceType

class OfficialInvestigator:
    """官方信源调查员：专门搜寻 SEC、交易所、官网发布的正式公告"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def search_official_announcements(self, ticker: str) -> List[ContentItem]:
        """
        通过定向搜索指令寻找官方公告。
        """
        results = []
        
        # 区分美股和 A 股的搜索策略
        if ".SS" in ticker or ".SZ" in ticker:
            # A 股定向搜寻巨潮资讯或交易所
            query = f"{ticker} site:cninfo.com.cn 公告 报告"
        elif ".HK" in ticker:
            # 港股搜寻披露易
            query = f"{ticker} site:hkexnews.hk 公告"
        else:
            # 美股搜寻 SEC 或官方新闻稿
            query = f"{ticker} site:sec.gov filings OR site:prnewswire.com"

        self.logger.info(f"⚖️  Searching official filings: {query}")
        
        try:
            with DDGS() as ddgs:
                search_results = ddgs.text(query, max_results=5)
                for r in search_results:
                    results.append(ContentItem(
                        id=r.get('href'),
                        title=f"[OFFICIAL] {r.get('title', '')}",
                        content=r.get('body', ''),
                        url=r.get('href'),
                        source_type=SourceType.SEC_FILING if "sec.gov" in r.get('href') else SourceType.NEWS,
                        author="Official Source",
                        publish_time=datetime.now(timezone.utc)
                    ))
        except Exception as e:
            self.logger.error(f"❌ Official filings search failed: {e}")
            
        return results
