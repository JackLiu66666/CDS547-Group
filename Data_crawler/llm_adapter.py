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

# ===================== 新增：大模型关键词提取（解决英文筛选问题） =====================
import os
import openai
from dotenv import load_dotenv

# 加载项目根目录下的 apikey.env 文件
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
apikey_env_path = os.path.join(project_root, 'apikey.env')
load_dotenv(dotenv_path=apikey_env_path)

# 使用 DeepSeek API 替代 OpenAI API
client = openai.OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1"
)

def extract_secondary_keywords(text: str, is_english: bool = True) -> list:
    """
    专为二次标签筛选设计：提取核心关键词，自动过滤the/and/of等无用词
    :param text: 新闻正文
    :param is_english: 是否英文新闻
    :return: 筛选用关键词列表
    """
    if not text:
        return []
    
    # 英文专属Prompt：强制过滤停用词，解决你的核心问题！
    if is_english:
        prompt = """
        Extract 5-10 core keywords for news filtering.
        RULES:
        1. NO stop words (the/and/of/in/on/at/a/an/is/are)
        2. Only nouns, proper nouns, key phrases
        3. Sort by importance
        4. Output ONLY comma-separated keywords, no other text
        """
    else:
        prompt = "提取5-10个新闻核心关键词，仅输出逗号分隔的词汇"

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": f"{prompt}\n\nText: {text}"}],
            temperature=0.1
        )
        keywords = [k.strip() for k in response.choices[0].message.content.split(",")]
        return [k for k in keywords if k]
    except Exception as e:
        print(f"关键词提取失败: {e}")
        return []
