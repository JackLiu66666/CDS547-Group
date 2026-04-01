from abc import ABC, abstractmethod
from typing import List

from src.models import Article


class BaseCrawler(ABC):
    """Base crawler interface for all source-specific crawlers."""

    @abstractmethod
    def crawl(self, query: str, max_items: int = 20) -> List[Article]:
        raise NotImplementedError
