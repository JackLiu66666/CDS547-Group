from __future__ import annotations

import hashlib
from typing import List, Optional

from bs4 import BeautifulSoup

from models import Article
from storage import ArticleStorage
from .base import BaseCrawler


class TencentNewsCrawler(BaseCrawler):
    """
    腾讯新闻爬虫
    - 从腾讯新闻首页获取新闻列表
    - 解析具体新闻页面获取完整内容
    """

    def _build_id(self, url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]

    def _parse_article(self, url: str, html: str) -> Optional[Article]:
        soup = BeautifulSoup(html, "html.parser")

        # 标题
        title_node = soup.find("h1", class_="article-title")
        if not title_node:
            title_node = soup.find("h1")
        title = title_node.get_text(strip=True) if title_node else "(no title)"

        # 作者
        author_node = soup.find("span", class_="article-source")
        author = author_node.get_text(strip=True) if author_node else None

        # 发布时间
        publish_meta = soup.find("meta", attrs={"property": "article:published_time"})
        published_at = publish_meta.get("content") if publish_meta else None

        # 正文内容
        content_node = soup.find("div", class_="content-article")
        if not content_node:
            content_node = soup.find("article")
        
        if content_node:
            paragraphs = [p.get_text(strip=True) for p in content_node.find_all("p")]
            content = "\n".join([p for p in paragraphs if p])
        else:
            content = ""
        
        if not content:
            return None

        article = Article(
            id=self._build_id(url),
            source="tencent_news",
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
        storage: Optional[ArticleStorage] = None,
        max_items: int = 50,
    ) -> List[Article]:
        """
        批量抓取腾讯新闻。

        - storage: ArticleStorage 实例；如果 None，则使用默认路径
        - max_items: 最大抓取数量
        """
        storage = storage or ArticleStorage()
        collected: List[Article] = []
        
        # 腾讯新闻首页
        list_url = "https://news.qq.com/"
        resp = self.get(list_url)
        
        if not resp or resp.status_code != 200:
            return collected
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # 提取新闻链接
        news_urls = []
        for a in soup.find_all("a"):
            href = a.get("href")
            if href and "news.qq.com/a/" in href:
                news_urls.append(href)
        
        # 去重
        news_urls = list(set(news_urls))
        
        for url in news_urls[:max_items]:
            page_resp = self.get(url)
            if not page_resp or page_resp.status_code != 200:
                continue
            
            article = self._parse_article(url, page_resp.text)
            if not article:
                continue
            
            if storage.save_article(article):
                collected.append(article)

        return collected