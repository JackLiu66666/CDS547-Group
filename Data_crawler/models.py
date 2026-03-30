from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class Article:
    """
    标准化后的文章数据结构。
    所有数据源都必须转换为该结构，方便后续统一处理 / 入库 / LLM 预处理。
    """

    # 唯一标识（建议为 url 的稳定哈希或数据源原始 ID）
    id: str

    # 信息源类型，如: "zhihu", "sina_news", "wechat"
    source: str

    # 标题、正文
    title: str
    content: str

    # 作者（可能缺失）
    author: Optional[str]

    # 发布时间（统一为 ISO8601 字符串，UTC 或本地时间）
    published_at: Optional[str]

    # 抓取时间（ISO8601）
    crawled_at: str

    # 原文链接
    url: str

    # 原始标签 / 话题等，统一放在此处，具体结构由各源决定
    raw_tags: Optional[Dict[str, Any]]

    # 预留字段，便于后续扩展（例如原始 JSON、来源频道等）
    extra: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def now_iso() -> str:
        return datetime.utcnow().isoformat()

