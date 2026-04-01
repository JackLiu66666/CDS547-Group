import json
from typing import List

import requests
from bs4 import BeautifulSoup

from src.crawlers.base import BaseCrawler
from src.models import Article


class ZhihuCrawler(BaseCrawler):
    """Zhihu search crawler via public search endpoint."""

    def crawl(self, query: str, max_items: int = 20) -> List[Article]:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            )
        }
        url = "https://www.zhihu.com/search"
        params = {"type": "content", "q": query}
        result: List[Article] = []

        try:
            resp = requests.get(url, params=params, headers=headers, timeout=12)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            script = soup.find("script", id="js-initialData")
            if not script:
                return result

            data = json.loads(script.text)
            search_result = data.get("initialState", {}).get("search", {}).get("searchResult", {})
            docs = search_result.get("items", [])
            for item in docs[:max_items]:
                obj = item.get("object", {})
                title = BeautifulSoup(obj.get("title", ""), "html.parser").get_text(" ", strip=True)
                content = BeautifulSoup(obj.get("excerpt", ""), "html.parser").get_text(" ", strip=True)
                article = Article(
                    source_type="知乎",
                    source_name="Zhihu",
                    title=title or "知乎内容",
                    url=obj.get("url", ""),
                    content=content,
                )
                result.append(article)
        except Exception:
            # Graceful fallback keeps pipeline available for demo.
            pass

        return result
