import json
from pathlib import Path
from typing import List

from src.models import Article


def save_articles_json(path: Path, articles: List[Article]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump([a.to_dict() for a in articles], f, ensure_ascii=False, indent=2)
    return path


def load_sample_dataset(path: Path) -> List[Article]:
    if not path.exists():
        return []
    records: List[Article] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            records.append(
                Article(
                    source_type=obj.get("source_type", "Sample"),
                    source_name=obj.get("source_name", "builtin"),
                    title=obj.get("title", ""),
                    url=obj.get("url", ""),
                    content=obj.get("content", ""),
                    publish_time=obj.get("publish_time", ""),
                    tags=obj.get("tags", []),
                    score=float(obj.get("score", 0.5)),
                )
            )
    return records
