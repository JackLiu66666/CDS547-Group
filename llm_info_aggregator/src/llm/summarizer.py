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
                f"[{idx+1}] Title: {a.title}\nSource: {a.source_type}/{a.source_name}\nContent: {a.content[:280]}"
                for idx, a in enumerate(articles[:20])
            ]
        )
        return (
            "You are an information analysis assistant. Please generate a personalized summary around the user's interest tag.\n"
            f"Interest Tag: {interest_tag}\n"
            f"Output requirements: 1) Cover core points and conclusions 2) Cite important sources 3) Provide actionable suggestions 4) Total length not exceeding {max_chars} characters.\n"
            "Please output in English, divided into: Core Conclusions, Key Developments, Action Suggestions.\n\n"
            f"Materials:\n{snippet}"
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
            top_titles = "; ".join([x.title for x in items[:5]])
            key_points = " ".join([x.content[:60] for x in items[:5]])
            fallback = (
                f"Core Conclusions: Recent information around '{tag}' shows key topics including: {top_titles}.\n"
                f"Key Developments: {key_points[: max_chars // 2]}\n"
                "Action Suggestions: Prioritize reading original content from high-quality sources and establish a weekly review checklist."
            )
            results[tag] = fallback[:max_chars]
        return results
