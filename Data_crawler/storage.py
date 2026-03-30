from __future__ import annotations

import json
import os
from typing import Iterable, Set

from models import Article


class ArticleStorage:
    """
    使用 JSON Lines 逐条写入，保证程序中途崩溃时，已抓取的数据不会丢失。
    同时维护一个已存在 ID 集合，用于增量抓取与去重。
    """

    def __init__(self, path: str = "data/raw_articles.jsonl") -> None:
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._existing_ids: Set[str] = set()
        self._load_existing_ids()

    @property
    def existing_ids(self) -> Set[str]:
        return self._existing_ids

    def _load_existing_ids(self) -> None:
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        _id = obj.get("id")
                        if _id:
                            self._existing_ids.add(_id)
                    except json.JSONDecodeError:
                        # 跳过坏行，避免影响整体加载
                        continue
        except OSError:
            # 读取失败时不抛异常，允许后续写入新文件
            return

    def save_article(self, article: Article) -> bool:
        """
        写入单条 Article。
        - 如果 ID 已存在，则直接返回 False（用于增量抓取）
        - 写入成功则返回 True
        """
        if article.id in self._existing_ids:
            return False

        try:
            with open(self.path, "a", encoding="utf-8") as f:
                json_line = json.dumps(article.to_dict(), ensure_ascii=False)
                f.write(json_line + "\n")
            self._existing_ids.add(article.id)
            return True
        except OSError:
            return False

    def save_articles(self, articles: Iterable[Article]) -> int:
        """
        批量写入，返回本次实际新增的数量。
        """
        count = 0
        for article in articles:
            if self.save_article(article):
                count += 1
        return count

