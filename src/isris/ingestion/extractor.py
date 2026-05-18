import logging
import trafilatura
import httpx
from typing import Optional

class DeepExtractor:
    """深度提取器：进入网页，剥离广告和杂质，提取核心正文"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    async def fetch_full_text(self, url: str) -> Optional[str]:
        """
        异步抓取并提取网页正文。
        """
        self.logger.info(f"🕸️  Extracting full text from: {url}")
        
        try:
            async with httpx.AsyncClient(timeout=15.0, headers=self.headers, follow_redirects=True) as client:
                response = await client.get(url)
                if response.status_code != 200:
                    self.logger.warning(f"Failed to fetch {url}, status: {response.status_code}")
                    return None
                
                # 使用 trafilatura 提取正文
                downloaded = response.text
                result = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
                
                if result:
                    self.logger.info(f"✅ Extracted {len(result)} characters from {url}")
                    return result
                else:
                    self.logger.warning(f"No content extracted from {url}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error during extraction from {url}: {e}")
            return None
