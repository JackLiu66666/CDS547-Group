from datetime import datetime
from typing import Dict, List, Tuple

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from utils import deduplicate_items, normalize_text


class CrossPlatformCrawler:
    """
    Cross-platform crawler.
    Supports Zhihu, WeChat Official Accounts, news, academic summaries, and returns crawl statistics for each information source.
    """

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            )
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        retry = Retry(
            total=2,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.mount("http://", HTTPAdapter(max_retries=retry))

    def crawl(self, keyword: str, selected_sources: List[str], max_items: int = 30) -> Tuple[List[Dict], Dict[str, Dict]]:
        all_items: List[Dict] = []
        stats: Dict[str, Dict] = {}
        source_map = {
            "Google News RSS": self._crawl_news,
            "Bing News RSS": self._crawl_bing_news,
            "arXiv": self._crawl_arxiv,
            "Hacker News": self._crawl_hackernews,
            "GitHub Repos": self._crawl_github,
            "Wikipedia": self._crawl_wikipedia,
            "StackOverflow": self._crawl_stackoverflow,
        }
        for source in selected_sources:
            func = source_map.get(source)
            if not func:
                continue
            try:
                data = func(keyword, max_items)
                all_items.extend(data)
                stats[source] = {"success": len(data) > 0, "count": len(data), "error": ""}
            except Exception as e:
                stats[source] = {"success": False, "count": 0, "error": str(e)}
        return deduplicate_items(all_items), stats

    def _crawl_news(self, keyword: str, max_items: int) -> List[Dict]:
        rss_url = f"https://news.google.com/rss/search?q={keyword}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
        resp = self.session.get(rss_url, timeout=self.timeout)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.content, "xml")
        nodes = soup.find_all("item")[:max_items]
        rows = []
        for node in nodes:
            rows.append(
                {
                    "title": normalize_text(node.title.get_text(strip=True) if node.title else ""),
                    "content": normalize_text(node.description.get_text(strip=True) if node.description else ""),
                    "source_type": "General News",
                    "source_name": "GoogleNewsRSS",
                    "publish_time": node.pubDate.get_text(strip=True) if node.pubDate else "",
                    "url": node.link.get_text(strip=True) if node.link else "",
                }
            )
        return rows

    def _crawl_bing_news(self, keyword: str, max_items: int) -> List[Dict]:
        rss_url = f"https://www.bing.com/news/search?q={keyword}&format=rss&mkt=zh-CN"
        resp = self.session.get(rss_url, timeout=self.timeout)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.content, "xml")
        nodes = soup.find_all("item")[:max_items]
        rows = []
        for node in nodes:
            rows.append(
                {
                    "title": normalize_text(node.title.get_text(strip=True) if node.title else ""),
                    "content": normalize_text(node.description.get_text(strip=True) if node.description else ""),
                    "source_type": "General News",
                    "source_name": "BingNewsRSS",
                    "publish_time": node.pubDate.get_text(strip=True) if node.pubDate else "",
                    "url": node.link.get_text(strip=True) if node.link else "",
                }
            )
        return rows

    def _crawl_arxiv(self, keyword: str, max_items: int) -> List[Dict]:
        url = (
            "http://export.arxiv.org/api/query?"
            f"search_query=all:{keyword}&start=0&max_results={max_items}&sortBy=submittedDate"
        )
        resp = self.session.get(url, timeout=self.timeout)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.content, "xml")
        nodes = soup.find_all("entry")
        rows = []
        for node in nodes:
            rows.append(
                {
                    "title": normalize_text(node.title.get_text(strip=True) if node.title else ""),
                    "content": normalize_text(node.summary.get_text(strip=True) if node.summary else ""),
                    "source_type": "Academic Summary",
                    "source_name": "arXiv",
                    "publish_time": node.published.get_text(strip=True) if node.published else "",
                    "url": node.id.get_text(strip=True) if node.id else "",
                }
            )
        return rows

    def _crawl_hackernews(self, keyword: str, max_items: int) -> List[Dict]:
        url = "https://hn.algolia.com/api/v1/search"
        resp = self.session.get(
            url,
            params={"query": keyword, "tags": "story", "hitsPerPage": max_items},
            timeout=self.timeout,
        )
        if resp.status_code != 200:
            return []
        payload = resp.json()
        hits = payload.get("hits", [])
        rows = []
        for hit in hits:
            title = normalize_text(hit.get("title") or hit.get("story_title") or "")
            url_value = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
            content = normalize_text(hit.get("story_text") or hit.get("comment_text") or "")
            rows.append(
                {
                    "title": title,
                    "content": content,
                    "source_type": "Technical Community",
                    "source_name": "HackerNews",
                    "publish_time": hit.get("created_at", ""),
                    "url": url_value,
                }
            )
        return rows

    def _crawl_github(self, keyword: str, max_items: int) -> List[Dict]:
        url = "https://api.github.com/search/repositories"
        resp = self.session.get(
            url,
            params={"q": keyword, "sort": "stars", "order": "desc", "per_page": min(max_items, 50)},
            timeout=self.timeout,
        )
        if resp.status_code != 200:
            return []
        payload = resp.json()
        rows = []
        for repo in payload.get("items", []):
            rows.append(
                {
                    "title": normalize_text(repo.get("full_name", "")),
                    "content": normalize_text(repo.get("description", "")),
                    "source_type": "Open Source Project",
                    "source_name": "GitHub",
                    "publish_time": repo.get("updated_at", ""),
                    "url": repo.get("html_url", ""),
                }
            )
        return rows

    def _crawl_wikipedia(self, keyword: str, max_items: int) -> List[Dict]:
        url = "https://en.wikipedia.org/w/api.php"
        resp = self.session.get(
            url,
            params={
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": keyword,
                "srlimit": max_items,
            },
            timeout=self.timeout,
        )
        if resp.status_code != 200:
            return []
        payload = resp.json()
        rows = []
        for item in payload.get("query", {}).get("search", []):
            title = item.get("title", "")
            rows.append(
                {
                    "title": normalize_text(title),
                    "content": normalize_text(item.get("snippet", "")),
                    "source_type": "Encyclopedia Knowledge",
                    "source_name": "Wikipedia",
                    "publish_time": datetime.now().strftime("%Y-%m-%d"),
                    "url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                }
            )
        return rows

    def _crawl_stackoverflow(self, keyword: str, max_items: int) -> List[Dict]:
        url = "https://api.stackexchange.com/2.3/search/advanced"
        resp = self.session.get(
            url,
            params={
                "order": "desc",
                "sort": "relevance",
                "q": keyword,
                "site": "stackoverflow",
                "pagesize": min(max_items, 50),
            },
            timeout=self.timeout,
        )
        if resp.status_code != 200:
            return []
        payload = resp.json()
        rows = []
        for q in payload.get("items", []):
            rows.append(
                {
                    "title": normalize_text(q.get("title", "")),
                    "content": normalize_text(" ".join(q.get("tags", []))),
                    "source_type": "Technical Q&A",
                    "source_name": "StackOverflow",
                    "publish_time": datetime.fromtimestamp(q.get("last_activity_date", 0)).strftime("%Y-%m-%d")
                    if q.get("last_activity_date")
                    else "",
                    "url": q.get("link", ""),
                }
            )
        return rows
