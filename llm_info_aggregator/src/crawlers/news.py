from typing import List

import requests
from bs4 import BeautifulSoup

from src.crawlers.base import BaseCrawler
from src.models import Article


class NewsCrawler(BaseCrawler):
    """General news crawler based on Google News RSS."""

    def crawl(self, query: str, max_items: int = 20) -> List[Article]:
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
        headers = {"User-Agent": "Mozilla/5.0"}
        result: List[Article] = []

        try:
            resp = requests.get(rss_url, headers=headers, timeout=12)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "xml")
            items = soup.find_all("item")[:max_items]
            for node in items:
                result.append(
                    Article(
                        source_type="News",
                        source_name="GoogleNewsRSS",
                        title=(node.title.text if node.title else "").strip(),
                        url=(node.link.text if node.link else "").strip(),
                        content=(node.description.text if node.description else "").strip(),
                        publish_time=(node.pubDate.text if node.pubDate else "").strip(),
                    )
                )
        except Exception:
            pass

        return result
