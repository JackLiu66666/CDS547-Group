from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Dict, List


@dataclass
class Article:
    """Unified content model used across crawlers and processors."""

    source_type: str
    source_name: str
    title: str
    url: str
    content: str
    publish_time: str = ""
    tags: List[str] = field(default_factory=list)
    score: float = 0.0

    def to_dict(self) -> Dict:
        payload = asdict(self)
        payload["fetched_at"] = datetime.now().isoformat()
        return payload
