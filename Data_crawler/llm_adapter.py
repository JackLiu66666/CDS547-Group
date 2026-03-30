from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, List


def _read_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def process_data_for_llm(
    input_path: str = "data/raw_articles.jsonl",
    output_path: str = "data/llm_ready.jsonl",
) -> None:
    """
    将原始抓取数据整理为更利于 LLM 消化的格式。

    在此你可以：
    - 做清洗（去除超长文本、无标题、无正文的记录）
    - 做截断（例如只保留前 N 字）
    - 统一字段命名（id/source/title/content/meta/...）
    目前先做一个简单直通 + 轻量清洗，为后续扩展预留空间。
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    processed: List[Dict[str, Any]] = []
    for obj in _read_jsonl(input_path):
        title = (obj.get("title") or "").strip()
        content = (obj.get("content") or "").strip()
        if not title or not content:
            continue

        record = {
            "id": obj.get("id"),
            "source": obj.get("source"),
            "title": title,
            "content": content,
            "meta": {
                "author": obj.get("author"),
                "published_at": obj.get("published_at"),
                "crawled_at": obj.get("crawled_at"),
                "url": obj.get("url"),
                "raw_tags": obj.get("raw_tags"),
                "extra": obj.get("extra"),
            },
        }
        processed.append(record)

    with open(output_path, "w", encoding="utf-8") as f:
        for rec in processed:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"[LLM Adapter] 已生成 {len(processed)} 条记录 -> {output_path}")