import os
from typing import Dict, List

from openai import OpenAI

from src.models import Article


class LLMSummarizer:
    """Supports OpenAI-compatible APIs and fallback local summarization."""

    def __init__(self, base_url: str = "", api_key: str = "", model: str = "gpt-4o-mini"):
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model

    def _build_prompt(self, articles: List[Article], interest_tag: str, max_chars: int) -> str:
        snippet = "\n\n".join(
            [
                f"[{idx+1}] 标题: {a.title}\n来源: {a.source_type}/{a.source_name}\n内容: {a.content[:280]}"
                for idx, a in enumerate(articles[:20])
            ]
        )
        return (
            "你是信息分析助手。请围绕用户兴趣标签生成个性化摘要。\n"
            f"兴趣标签: {interest_tag}\n"
            f"输出要求: 1) 覆盖核心观点与结论 2) 标注重要来源 3) 可执行建议 4) 总长度不超过{max_chars}字。\n"
            "请使用中文输出，分成：核心结论、重点动态、行动建议。\n\n"
            f"素材如下:\n{snippet}"
        )

    def summarize(self, grouped: Dict[str, List[Article]], max_chars: int = 500) -> Dict[str, str]:
        results: Dict[str, str] = {}
        for tag, items in grouped.items():
            if self.api_key:
                try:
                    client = OpenAI(api_key=self.api_key, base_url=self.base_url)
                    prompt = self._build_prompt(items, tag, max_chars)
                    resp = client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "你是严谨的信息摘要专家。"},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.2,
                    )
                    text = resp.choices[0].message.content.strip()
                    results[tag] = text[:max_chars]
                    continue
                except Exception:
                    pass

            # Fallback summary: keep pipeline always runnable without API key.
            top_titles = "；".join([x.title for x in items[:5]])
            key_points = " ".join([x.content[:60] for x in items[:5]])
            fallback = (
                f"核心结论：围绕“{tag}”近期信息显示，重点主题包括：{top_titles}。\n"
                f"重点动态：{key_points[: max_chars // 2]}\n"
                "行动建议：优先阅读高质量来源原文并建立每周复盘清单。"
            )
            results[tag] = fallback[:max_chars]
        return results
