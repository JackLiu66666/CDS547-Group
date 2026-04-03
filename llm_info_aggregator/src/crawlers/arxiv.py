from typing import List

import requests
from bs4 import BeautifulSoup

from src.crawlers.base import BaseCrawler
from src.models import Article


class ArxivCrawler(BaseCrawler):
    """Academic paper crawler using arXiv API feed."""

    def crawl(self, query: str, max_items: int = 20) -> List[Article]:
        api = (
            "http://export.arxiv.org/api/query?"
            f"search_query=all:{query}&start=0&max_results={max_items}&sortBy=submittedDate"
        )
        result: List[Article] = []

        try:
            resp = requests.get(api, timeout=12)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "xml")
            entries = soup.find_all("entry")
            for entry in entries:
                authors = [n.text.strip() for n in entry.find_all("name")]
                content = (entry.summary.text if entry.summary else "").strip()
                if authors:
                    content = f"Authors: {', '.join(authors)}\n{content}"
                result.append(
                    Article(
                        source_type="Academic Paper",
                        source_name="arXiv",
                        title=(entry.title.text if entry.title else "").strip().replace("\n", " "),
                        url=(entry.id.text if entry.id else "").strip(),
                        content=content,
                        publish_time=(entry.published.text if entry.published else "").strip(),
                    )
                )
        except Exception:
            pass
        return result
