import re
from typing import Dict, List

import pandas as pd

from src.models import Article


def normalize_text(text: str) -> str:
    """Normalize whitespace and remove obvious html residues."""
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def deduplicate(articles: List[Article]) -> List[Article]:
    """Deduplicate by URL first, then by title+content hash."""
    seen = set()
    clean_items: List[Article] = []
    for item in articles:
        item.title = normalize_text(item.title)
        item.content = normalize_text(item.content)
        key = item.url or f"{item.title}|{item.content[:100]}"
        if key in seen or not item.title:
            continue
        seen.add(key)
        clean_items.append(item)
    return clean_items


def classify_by_tags(articles: List[Article], tags: List[str]) -> List[Article]:
    """Assign tags using simple keyword matching with score."""
    for item in articles:
        matched = []
        lowered = f"{item.title} {item.content}".lower()
        for tag in tags:
            if tag.lower() in lowered:
                matched.append(tag)
        item.tags = matched if matched else ["Uncategorized"]
        item.score = min(1.0, 0.3 + len(matched) * 0.2)
    return articles


def to_dataframe(articles: List[Article]) -> pd.DataFrame:
    return pd.DataFrame([x.to_dict() for x in articles])


def group_by_tag(articles: List[Article]) -> Dict[str, List[Article]]:
    grouped: Dict[str, List[Article]] = {}
    for item in articles:
        for tag in item.tags:
            grouped.setdefault(tag, []).append(item)
    return grouped
