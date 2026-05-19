import logging
from typing import List
from datetime import datetime, timezone
from duckduckgo_search import DDGS
from ..core.models import ContentItem, SourceType

class OfficialInvestigator:
    """官方信源调查员：搜寻权威公告"""

    def __init__(self):
        self.logger = logging.getLogger("isris.ingestion.filings")

    async def search_official_announcements(self, ticker: str) -> List[ContentItem]:
        if ".SS" in ticker or ".SZ" in ticker:
            query = f"{ticker} site:cninfo.com.cn 公告"
        elif ".HK" in ticker:
            query = f"{ticker} site:hkexnews.hk 公告"
        else:
            query = f"{ticker} site:sec.gov filings"

        self.logger.info(f"⚖️  Searching official filings: {query}")
        results = []
        
        try:
            with DDGS() as ddgs:
                try:
                    search_results = list(ddgs.text(query, max_results=5))
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
                except Exception:
                    pass
        except Exception as e:
            self.logger.error(f"❌ Official search failed: {e}")
            
        return results
