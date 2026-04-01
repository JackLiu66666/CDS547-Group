import json
from pathlib import Path
from typing import List


class TagManager:
    """Persistent CRUD for user custom interest tags."""

    def __init__(self, tag_file: Path):
        self.tag_file = tag_file
        self.tag_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.tag_file.exists():
            self.save_tags(["人工智能", "考研", "职场技能"])

    def load_tags(self) -> List[str]:
        try:
            with self.tag_file.open("r", encoding="utf-8") as f:
                tags = json.load(f)
            return sorted(list(set([t.strip() for t in tags if t.strip()])))
        except Exception:
            return ["人工智能", "考研", "职场技能"]

    def save_tags(self, tags: List[str]) -> None:
        clean_tags = sorted(list(set([t.strip() for t in tags if t.strip()])))
        with self.tag_file.open("w", encoding="utf-8") as f:
            json.dump(clean_tags, f, ensure_ascii=False, indent=2)

    def add_tag(self, tag: str) -> List[str]:
        tags = self.load_tags()
        if tag.strip() and tag not in tags:
            tags.append(tag.strip())
            self.save_tags(tags)
        return self.load_tags()

    def edit_tag(self, old_tag: str, new_tag: str) -> List[str]:
        tags = self.load_tags()
        tags = [new_tag.strip() if t == old_tag else t for t in tags]
        self.save_tags(tags)
        return self.load_tags()

    def delete_tag(self, tag: str) -> List[str]:
        tags = [t for t in self.load_tags() if t != tag]
        self.save_tags(tags)
        return self.load_tags()
