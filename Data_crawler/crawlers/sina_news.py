from __future__ import annotations

import hashlib
from datetime import datetime
from typing import List, Optional

from bs4 import BeautifulSoup

from models import Article
from storage import ArticleStorage
from .base import BaseCrawler


class SinaNewsCrawler(BaseCrawler):
    """
    使用新浪新闻公开的滚动新闻接口 + 文章页面解析。
    - 接口返回新闻列表（标题、链接、时间等）
    - 再进入具体新闻页解析正文，确保拿到完整文章内容
    """

    API_URL = "https://feed.mix.sina.com.cn/api/roll/get"

    def _build_id(self, url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]

    def _parse_datetime(self, ts: Optional[int]) -> Optional[str]:
        if not ts:
            return None
        try:
            dt = datetime.fromtimestamp(int(ts))
            return dt.isoformat()
        except Exception:
            return None

    def _in_date_range(
        self,
        published_dt: Optional[datetime],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> bool:
        if not published_dt:
            return True
        if start_date and published_dt < start_date:
            return False
        if end_date and published_dt > end_date:
            return False
        return True

    def _parse_article_content(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        # 新浪新闻主体常见结构：id="artibody" 或 class="article"
        candidates = [
            soup.find("div", id="artibody"),
            soup.find("div", attrs={"class": "article"}),
            soup.find("div", attrs={"class": "article-content"}),
        ]
        for node in candidates:
            if not node:
                continue
            paragraphs = [p.get_text(strip=True) for p in node.find_all("p")]
            text = "\n".join([p for p in paragraphs if p])
            if text:
                return text
        # 兜底：取整个页面的可见文本（可能会比较脏）
        return soup.get_text(separator="\n", strip=True)

    def crawl_batch(
        self,
        storage: Optional[ArticleStorage] = None,
        max_items: int = 50,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        channel_pageid: str = "153",
        channel_lid: str = "2509",
    ) -> List[Article]:
        """
        批量抓取新浪新闻。

        - storage: ArticleStorage 实例；如果 None，则使用默认路径
        - max_items: 最大抓取数量
        - start_date / end_date: 过滤发布时间，格式 "YYYY-MM-DD"
        - channel_pageid / channel_lid: 可根据新浪新闻不同频道调整
        """
        storage = storage or ArticleStorage()

        start_dt = (
            datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        )
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None

        collected: List[Article] = []
        page = 1

        while len(collected) < max_items:
            params = {
                "pageid": channel_pageid,
                "lid": channel_lid,
                "num": 50,
                "page": page,
            }
            resp = self.get(self.API_URL, params=params)
            if not resp or resp.status_code != 200:
                break

            try:
                data = resp.json()
            except ValueError:
                break

            items = data.get("result", {}).get("data") or []
            if not items:
                break

            for item in items:
                if len(collected) >= max_items:
                    break

                url = item.get("url")
                title = item.get("title")
                ts = item.get("ctime")
                published_iso = self._parse_datetime(ts)
                published_dt = (
                    datetime.fromtimestamp(int(ts)) if ts else None
                )

                if not url or not title:
                    continue

                if not self._in_date_range(published_dt, start_dt, end_dt):
                    continue

                page_resp = self.get(url)
                if not page_resp or page_resp.status_code != 200:
                    continue

                content = self._parse_article_content(page_resp.text)
                if not content:
                    continue

                article = Article(
                    id=self._build_id(url),
                    source="sina_news",
                    title=title,
                    content=content,
                    author=item.get("media_name") or None,
                    published_at=published_iso,
                    crawled_at=Article.now_iso(),
                    url=url,
                    raw_tags={
                        "keywords": item.get("keywords"),
                        "channel": item.get("channel"),
                    },
                    extra={"source_raw": item},
                )

                if storage.save_article(article):
                    collected.append(article)

            page += 1

        return collected

