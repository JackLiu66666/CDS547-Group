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
        ("人工智能", "大模型训练", "学术论文", "arXiv"),
        ("人工智能", "Agent系统", "知乎", "Zhihu"),
        ("人工智能", "多模态推理", "新闻", "GoogleNewsRSS"),
        ("考研", "数学复习", "知乎", "Zhihu"),
        ("考研", "英语阅读", "新闻", "EducationNews"),
        ("考研", "政治时政", "公众号", "考研订阅号"),
        ("职场技能", "项目管理", "新闻", "BusinessNews"),
        ("职场技能", "数据分析", "知乎", "Zhihu"),
        ("职场技能", "沟通协作", "公众号", "职场进阶"),
    ]

    with path.open("w", encoding="utf-8") as f:
        for idx in range(target_size):
            tag, subtopic, source_type, source_name = topics[idx % len(topics)]
            record = {
                "id": idx + 1,
                "source_type": source_type,
                "source_name": source_name,
                "title": f"{tag}-{subtopic}-实用信息第{idx+1}条",
                "url": f"https://example.com/{tag}/{idx+1}",
                "content": (
                    f"这是关于{tag}与{subtopic}的样本内容，用于离线演示信息聚合、分类与摘要流程。"
                    "内容包含方法、案例、常见误区和执行建议。"
                ),
                "publish_time": "2026-03-31",
                "tags": [tag],
                "score": 0.7,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path
