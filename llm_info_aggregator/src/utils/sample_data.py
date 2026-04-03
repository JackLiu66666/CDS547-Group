import json
from pathlib import Path


def ensure_sample_dataset(path: Path, target_size: int = 600) -> Path:
    """
    Ensure built-in labeled dataset exists with 500+ records.
    Records cover AI research, exam prep, and workplace skills.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as f:
                line_count = sum(1 for _ in f if _.strip())
            if line_count >= 500:
                return path
        except Exception:
            pass

    topics = [
        ("Artificial Intelligence", "Large Model Training", "Academic Paper", "arXiv"),
        ("Artificial Intelligence", "Agent Systems", "Zhihu", "Zhihu"),
        ("Artificial Intelligence", "Multimodal Reasoning", "News", "GoogleNewsRSS"),
        ("Graduate Exam", "Mathematics Review", "Zhihu", "Zhihu"),
        ("Graduate Exam", "English Reading", "News", "EducationNews"),
        ("Graduate Exam", "Political Current Affairs", "WeChat Official Account", "Graduate Exam Subscription"),
        ("Professional Skills", "Project Management", "News", "BusinessNews"),
        ("Professional Skills", "Data Analysis", "Zhihu", "Zhihu"),
        ("Professional Skills", "Communication and Collaboration", "WeChat Official Account", "Career Advancement"),
    ]

    with path.open("w", encoding="utf-8") as f:
        for idx in range(target_size):
            tag, subtopic, source_type, source_name = topics[idx % len(topics)]
            record = {
                "id": idx + 1,
                "source_type": source_type,
                "source_name": source_name,
                "title": f"{tag}-{subtopic}-Useful Information #{idx+1}",
                "url": f"https://example.com/{tag}/{idx+1}",
                "content": (
                    f"This is sample content about {tag} and {subtopic}, used for offline demonstration of information aggregation, classification, and summarization processes."
                    "Content includes methods, cases, common pitfalls, and execution suggestions."
                ),
                "publish_time": "2026-03-31",
                "tags": [tag],
                "score": 0.7,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path
