from typing import List

import requests
from bs4 import BeautifulSoup

from src.crawlers.base import BaseCrawler
from src.models import Article


class WechatCrawler(BaseCrawler):
    """
    WeChat public account content crawler (best effort).
    Uses Sogou Weixin search page; access may vary by network.
    """

    def crawl(self, query: str, max_items: int = 20) -> List[Article]:
        url = "https://weixin.sogou.com/weixin"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            )
        }
        params = {"type": 2, "query": query}
        result: List[Article] = []

        try:
            resp = requests.get(url, params=params, headers=headers, timeout=12)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            blocks = soup.select("ul.news-list li")[:max_items]
            for block in blocks:
                title_node = block.select_one("h3 a")
                content_node = block.select_one("p.txt-info")
                source_node = block.select_one("a.account")
                if not title_node:
                    continue
                result.append(
                    Article(
                        source_type="WeChat Official Account",
                        source_name=(source_node.get_text(strip=True) if source_node else "WeChat Official Platform"),
                        title=title_node.get_text(" ", strip=True),
                        url=title_node.get("href", ""),
                        content=content_node.get_text(" ", strip=True) if content_node else "",
                    )
                )
        except Exception:
            pass

        return result
