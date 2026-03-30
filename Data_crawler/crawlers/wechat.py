from __future__ import annotations

import hashlib
from typing import Iterable, List, Optional

from bs4 import BeautifulSoup

from models import Article
from storage import ArticleStorage
from .base import BaseCrawler


class WechatCrawler(BaseCrawler):
    """
    适用于微信公众号「公开文章链接」的爬虫。
    - 不涉及登录与私域内容
    - 仅针对已知的 mp.weixin.qq.com 文章 URL
    """

    def _build_id(self, url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]

    def _extract_text(self, node) -> str:
        if not node:
            return ""
        paragraphs = [p.get_text(strip=True) for p in node.find_all(["p", "section"])]
        text = "\n".join([p for p in paragraphs if p])
        if text:
            return text
        return node.get_text(separator="\n", strip=True)

    def _parse_article(self, url: str, html: str) -> Optional[Article]:
        soup = BeautifulSoup(html, "html.parser")

        # 标题
        title_node = soup.find("h1", id="activity-name")
        if not title_node:
            title_node = soup.find("meta", attrs={"property": "og:title"})
        title = (
            title_node.get_text(strip=True)
            if title_node and hasattr(title_node, "get_text")
            else title_node.get("content")
            if title_node
            else ""
        )

        # 作者
        author_node = soup.find("span", id="js_author_name")
        if not author_node:
            author_node = soup.find("meta", attrs={"name": "author"})
        author = (
            author_node.get_text(strip=True)
            if author_node and hasattr(author_node, "get_text")
            else author_node.get("content")
            if author_node
            else None
        )

        # 发布时间
        publish_meta = soup.find("meta", attrs={"property": "article:published_time"})
        published_at = publish_meta.get("content") if publish_meta else None

        # 正文内容
        content_node = soup.find("div", id="js_content")
        content = self._extract_text(content_node)
        if not content:
            return None

        # 原始标签（如分类、描述等）
        desc_meta = soup.find("meta", attrs={"property": "og:description"})
        raw_tags = {
            "description": desc_meta.get("content") if desc_meta else None,
        }

        article = Article(
            id=self._build_id(url),
            source="wechat",
            title=title or "(no title)",
            content=content,
            author=author,
            published_at=published_at,
            crawled_at=Article.now_iso(),
            url=url,
            raw_tags=raw_tags,
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
        批量抓取若干微信公众号公开文章链接。

        - urls: mp.weixin.qq.com 的文章 URL 列表
        - storage: ArticleStorage 实例；如果 None 则使用默认
        - max_items: 最多抓取多少条（用于控制批量抓取规模）
        """
        storage = storage or ArticleStorage()
        collected: List[Article] = []

        for idx, url in enumerate(urls):
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

