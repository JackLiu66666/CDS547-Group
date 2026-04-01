import json
import re
from typing import Dict, List

import requests


class DomesticLLM:
    """
    国内 OpenAI 兼容接口适配器。
    示例可用 base_url:
    - https://api.deepseek.com/v1
    - https://api.siliconflow.cn/v1
    """

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key.strip()
        self.base_url = base_url.strip()
        self.model = model.strip()

    def _responses_url(self) -> str:
        """Resolve Ark/OpenAI-compatible responses endpoint URL."""
        base = self.base_url.rstrip("/")
        if base.endswith("/responses"):
            return base
        if base.endswith("/v1") or base.endswith("/api/v3"):
            return f"{base}/responses"
        return f"{base}/responses"

    def _extract_text_from_responses(self, data: Dict) -> str:
        """Parse output text from Responses API result."""
        if isinstance(data.get("output_text"), str) and data.get("output_text"):
            return data["output_text"].strip()

        output = data.get("output", [])
        chunks: List[str] = []
        for item in output:
            for c in item.get("content", []):
                # 兼容不同字段命名
                text = c.get("text") or c.get("value")
                if text:
                    chunks.append(str(text))
        return "\n".join(chunks).strip()

    def _call_llm_text(self, prompt: str, temperature: float = 0.2, system_prompt: str = "") -> str:
        """
        Call model using Responses API.
        Works with Volcengine Ark endpoint by default.
        """
        if not (self.api_key and self.base_url and self.model):
            return ""

        url = self._responses_url()
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        input_payload = []
        if system_prompt.strip():
            input_payload.append(
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt.strip()}],
                }
            )
        input_payload.append({"role": "user", "content": [{"type": "input_text", "text": prompt}]})
        payload = {"model": self.model, "input": input_payload, "temperature": temperature}

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            if resp.status_code >= 300:
                return ""
            data = resp.json()
            return self._extract_text_from_responses(data)
        except Exception:
            return ""

    def _extract_json(self, raw: str, object_mode: bool = True):
        if not raw:
            return None
        pattern = r"\{[\s\S]*\}" if object_mode else r"\[[\s\S]*\]"
        m = re.search(pattern, raw)
        candidate = m.group(0) if m else raw
        try:
            return json.loads(candidate)
        except Exception:
            return None

    def summarize_by_interest(
        self,
        items: List[Dict],
        tags: List[str],
        keyword: str,
        summary_len: int = 500,
        use_interest_tags: bool = True,
    ) -> Dict[str, str]:
        grouped = self._group_items(items, tags, keyword, use_interest_tags)
        output = {}
        for tag, rows in grouped.items():
            output[tag] = self._one_tag_summary(rows, tag, keyword, summary_len)
        return output

    def pre_analyze_results(
        self, items: List[Dict], keyword: str, summary_len: int = 500, top_k_tags: int = 10
    ) -> Dict[str, object]:
        """
        第一阶段：LLM对检索结果做预分析，输出
        1) 总结摘要
        2) 推荐兴趣标签（供用户二次选择）
        """
        if not items:
            return {"overview": "暂无可用信息。", "recommended_tags": []}

        refs = "\n".join(
            [
                f"[{i+1}] 标题:{r.get('title', '')} | 来源:{r.get('source_type', '')}/{r.get('source_name', '')} | 内容:{r.get('content', '')[:180]}"
                for i, r in enumerate(items[:50])
            ]
        )

        if self.api_key and self.base_url and self.model:
            try:
                prompt = (
                    f"请分析用户搜索词“{keyword}”对应的信息集合，并输出 JSON。\n"
                    "JSON字段:\n"
                    "- overview: 对结果的高质量中文总结（覆盖核心观点，简洁清楚）\n"
                    f"- tags: 最多{top_k_tags}个可用于二次筛选的兴趣标签（2-8字短语，避免“信息/新闻/相关”这类泛词）\n"
                    "仅输出JSON对象，不要任何解释。\n\n"
                    f"候选信息:\n{refs}"
                )
                raw = self._call_llm_text(prompt, temperature=0.2)
                data = self._extract_json(raw, object_mode=True) or {}
                overview = str(data.get("overview", "")).strip()
                tags = data.get("tags", [])
                tags = [str(x).strip() for x in tags if str(x).strip()]
                tags = self._clean_tags(tags, keyword)[:top_k_tags]
                if overview or tags:
                    return {
                        "overview": (overview or "已完成预分析。")[:summary_len],
                        "recommended_tags": tags[:top_k_tags],
                    }
            except Exception:
                pass

        # 本地回退：关键词提取 + 拼接总结
        tags = self.extract_focus_keywords(items, keyword, top_k=top_k_tags)
        head_titles = "；".join([x.get("title", "") for x in items[:6]])
        overview = (
            f"围绕“{keyword}”共检索到{len(items)}条信息。"
            f"主要主题包括：{head_titles}。"
            "建议先从推荐标签中选择方向，再查看二次精准结果。"
        )
        return {"overview": overview[:summary_len], "recommended_tags": tags}

    def _clean_tags(self, tags: List[str], keyword: str) -> List[str]:
        bad = {"信息", "新闻", "相关", "动态", "内容", "资料", "推荐", "平台", "搜索"}
        out = []
        for t in tags:
            t = re.sub(r"[#*`\"'，,。；;:：\[\]\(\)（）]+", "", t).strip()
            if not t or len(t) < 2 or len(t) > 18:
                continue
            if t in bad:
                continue
            if t.lower() == keyword.lower():
                continue
            if t not in out:
                out.append(t)
        return out

    def extract_focus_keywords(self, items: List[Dict], keyword: str, top_k: int = 12) -> List[str]:
        """
        从搜索结果中提取可用于二次筛选的关键词。
        有 API 时优先走 LLM，无 API 时使用本地高频词回退。
        """
        if not items:
            return []

        if self.api_key and self.base_url and self.model:
            try:
                refs = "\n".join(
                    [f"- {r.get('title', '')} {r.get('content', '')[:120]}" for r in items[:30]]
                )
                prompt = (
                    f"请从以下与“{keyword}”相关的信息中，提取{top_k}个最有区分度的关键词。"
                    "输出要求：仅输出 JSON 数组，如 [\"词1\",\"词2\"]，不要输出其他文字。\n"
                    f"{refs}"
                )
                raw = self._call_llm_text(prompt, temperature=0.1)
                # 尽量鲁棒地解析模型输出，避免因为额外说明文字导致解析失败。
                arr = self._extract_json(raw, object_mode=False)
                if isinstance(arr, list):
                    kws = [str(x).strip() for x in arr if str(x).strip()]
                    if kws:
                        return self._clean_tags(kws, keyword)[:top_k]
                # 兼容“关键词1,关键词2”这类非JSON输出
                alt = re.split(r"[，,、\n]+", raw)
                alt = [x.strip(" -•\t\r ") for x in alt if x.strip()]
                if alt:
                    return self._clean_tags(alt, keyword)[:top_k]
            except Exception:
                pass

        # 本地回退
        import re
        from collections import Counter

        stop_words = {
            "我们",
            "你们",
            "他们",
            "这个",
            "一个",
            "以及",
            "进行",
            "相关",
            "信息",
            "内容",
            "用户",
            "平台",
            "可以",
            "通过",
            "关于",
            "如何",
            "这是",
            "使用",
        }
        text = " ".join([f"{x.get('title', '')} {x.get('content', '')}" for x in items[:80]])
        words = re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]{2,12}", text)
        words = [w for w in words if w not in stop_words and w.lower() != keyword.lower()]
        top = [w for w, _ in Counter(words).most_common(top_k * 2)]
        uniq = []
        for w in top:
            if w not in uniq:
                uniq.append(w)
        return uniq[:top_k]

    def semantic_filter_items(
        self,
        items: List[Dict],
        keyword: str,
        selected_keywords: List[str],
        top_n: int = 60,
    ) -> List[Dict]:
        """
        基于 LLM API 对候选结果做语义相关性筛选与排序。
        返回最相关的 top_n 条；若调用失败则回退原始列表。
        """
        if not items:
            return []
        if not (self.api_key and self.base_url and self.model):
            return items[:top_n]

        refs = []
        for i, row in enumerate(items[:120], start=1):
            refs.append(
                f"[{i}] 标题:{row.get('title','')} | 来源:{row.get('source_type','')} | 内容:{row.get('content','')[:180]}"
            )
        focus = "、".join([x for x in selected_keywords if x.strip()]) or "无"
        prompt = (
            f"请从候选信息中筛选最相关内容。\n"
            f"用户搜索词: {keyword}\n"
            f"用户选中的关注关键词: {focus}\n"
            "任务: 按相关性从高到低挑选最相关条目，返回 JSON 数组，仅包含编号数字，例如 [2,5,9]。\n"
            f"最多返回 {top_n} 条，不要输出任何解释文字。\n\n"
            "候选信息:\n" + "\n".join(refs)
        )
        try:
            raw = self._call_llm_text(prompt, temperature=0.1)
            idx_arr = self._extract_json(raw, object_mode=False) or []
            picked = []
            for idx in idx_arr:
                if isinstance(idx, int) and 1 <= idx <= min(len(items), 120):
                    picked.append(items[idx - 1])
            return picked[:top_n] if picked else items[:top_n]
        except Exception:
            return items[:top_n]

    def _group_items(
        self, items: List[Dict], tags: List[str], keyword: str, use_interest_tags: bool
    ) -> Dict[str, List[Dict]]:
        if not use_interest_tags:
            # 纯搜索摘要模式：兴趣标签不参与分组，仅按搜索词整体总结。
            return {"搜索词总结": items[:80] if items else []}

        groups: Dict[str, List[Dict]] = {tag: [] for tag in tags if tag.strip()}
        groups["自由搜索"] = []
        for item in items:
            text = f"{item.get('title', '')} {item.get('content', '')}".lower()
            matched = False
            for tag in list(groups.keys()):
                if tag != "自由搜索" and tag.lower() in text:
                    groups[tag].append(item)
                    matched = True
            if keyword.lower() in text and not matched:
                groups["自由搜索"].append(item)
        if not groups["自由搜索"]:
            groups["自由搜索"] = items[:20]
        return {k: v for k, v in groups.items() if v}

    def _one_tag_summary(self, rows: List[Dict], tag: str, keyword: str, summary_len: int) -> str:
        if not rows:
            return "暂无可用信息。"
        prompt = self._build_prompt(rows, tag, keyword, summary_len)

        if self.api_key and self.base_url and self.model:
            try:
                text = self._call_llm_text(
                    prompt,
                    temperature=0.2,
                    system_prompt="你是严谨的信息分析助手，只输出与用户兴趣相关内容。",
                ).strip()
                if text:
                    return text[:summary_len]
            except Exception:
                pass

        # 本地回退摘要，保证 Demo 无 Key 也能运行
        titles = "；".join([r.get("title", "") for r in rows[:6]])
        points = " ".join([r.get("content", "")[:50] for r in rows[:6]])
        return (
            f"核心结论：围绕“{tag}”与“{keyword}”的重点信息包括：{titles}。\n"
            f"重点动态：{points[: summary_len // 2]}\n"
            "行动建议：优先跟踪高频关键词，结合原文建立每周学习与复盘清单。"
        )[:summary_len]

    def _build_prompt(self, rows: List[Dict], tag: str, keyword: str, summary_len: int) -> str:
        ref = "\n\n".join(
            [
                f"[{i+1}] 标题:{r.get('title', '')}\n来源:{r.get('source_type', '')}/{r.get('source_name', '')}\n内容:{r.get('content', '')[:300]}"
                for i, r in enumerate(rows[:20])
            ]
        )
        return (
            f"请围绕用户搜索词“{keyword}”与兴趣标签“{tag}”生成定向摘要。\n"
            "要求：\n"
            "1. 仅保留相关信息，拒绝无关内容；\n"
            "2. 输出结构为：核心结论、重点动态、行动建议；\n"
            f"3. 总字数不超过{summary_len}字；\n"
            "4. 覆盖信息中的关键观点与来源。\n\n"
            f"输入信息如下：\n{ref}"
        )
