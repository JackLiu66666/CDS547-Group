from __future__ import annotations

import hashlib
from typing import Iterable, List, Optional

from bs4 import BeautifulSoup

from models import Article
from storage import ArticleStorage
from .base import BaseCrawler


class ZhihuCrawler(BaseCrawler):
    """
    知乎爬虫（示例实现）：
    - 为降低反爬风险，示例默认从「已给定的知乎文章链接（专栏文章）」抓取内容；
    - 你也可以扩展为从知乎热榜 / 搜索结果页解析出文章链接后再调用本爬虫。
    - 建议仅针对 https://zhuanlan.zhihu.com/p/XXXXXX 这类专栏文章 URL。
    """

    def _build_id(self, url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]

    def _extract_text(self, node) -> str:
        if not node:
            return ""
        paragraphs = [p.get_text(strip=True) for p in node.find_all(["p", "blockquote"])]
        text = "\n".join([p for p in paragraphs if p])
        if text:
            return text
        return node.get_text(separator="\n", strip=True)

    def _parse_article(self, url: str, html: str) -> Optional[Article]:
        soup = BeautifulSoup(html, "html.parser")

        # 标题：优先 article > h1，其次 <title>
        title_node = soup.find("h1")
        if not title_node:
            title_node = soup.find("title")
        title = title_node.get_text(strip=True) if title_node else "(no title)"

        # 作者（知乎专栏常见选择器可能变动，此处做兼容性较强的兜底方案）
        author_node = soup.find(attrs={"class": lambda c: c and "AuthorInfo-head" in c})
        author = None
        if author_node:
            name_node = author_node.find("meta", attrs={"itemprop": "name"})
            if name_node and name_node.get("content"):
                author = name_node.get("content")

        # 发布时间：有些页面会包含 meta[itemprop="datePublished"]
        publish_meta = soup.find("meta", attrs={"itemprop": "datePublished"})
        published_at = publish_meta.get("content") if publish_meta else None

        # 正文内容：知乎专栏文章常见 class 为 RichText ztext Post-RichText
        content_node = soup.find(
            "div",
            attrs={
                "class": lambda c: c
                and "RichText" in c
                and ("Post-RichText" in c or "Article" in c)
            },
        )
        if not content_node:
            # 兜底：寻找 article 标签
            content_node = soup.find("article")
        content = self._extract_text(content_node) if content_node else ""
        if not content:
            return None

        article = Article(
            id=self._build_id(url),
            source="zhihu",
            title=title,
            content=content,
            author=author,
            published_at=published_at,
            crawled_at=Article.now_iso(),
            url=url,
            raw_tags=None,
            extra=None,
        )
        return article

    def crawl_batch(
        self,
        urls: Iterable[str],
        storage: Optional[ArticleStorage] = None,
        max_items: Optional[int] = None,
    ) -> List[Article]:
        """
        批量抓取知乎专栏文章。

        - urls: zhuanlan.zhihu.com 的文章 URL 列表
        - storage: ArticleStorage 实例；如果 None 则使用默认
        - max_items: 最多抓取多少条（用于控制批量抓取规模）
        """
        storage = storage or ArticleStorage()
        collected: List[Article] = []

        for url in urls:
            if max_items is not None and len(collected) >= max_items:
                break

            resp = self.get(url)
            if not resp or resp.status_code != 200:
                continue

            article = self._parse_article(url, resp.text)
            if not article:
                continue

            if storage.save_article(article):
                collected.append(article)

        return collected

