import json
import re
from typing import Dict, List

import requests


class DomesticLLM:
    """
    Domestic OpenAI-compatible interface adapter.
    Example available base_url:
    - https://api.deepseek.com (Note: without /v1)
    - https://api.siliconflow.cn/v1
    - https://ark.cn-beijing.volces.com/api/v3
    """

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key.strip()
        self.base_url = base_url.strip()
        self.model = model.strip()
        self.debug_info = []  # 添加调试信息列表

    def _is_volcengine_ark(self) -> bool:
        """Check if it is Volcengine Ark format"""
        return "/api/v3" in self.base_url or "volces.com" in self.base_url

    def _chat_completions_url(self) -> str:
        """Resolve OpenAI-compatible chat completions endpoint URL."""
        base = self.base_url.rstrip("/")
        # 如果已经是 v1 结尾，拼接 /chat/completions
        if base.endswith("/v1"):
            return f"{base}/chat/completions"
        # 如果是域名格式（如 DeepSeek），自动添加 /v1/chat/completions
        return f"{base}/v1/chat/completions"

    def _extract_text_from_chat(self, data: Dict) -> str:
        """Parse output text from Chat Completions API result (OpenAI format)."""
        try:
            choices = data.get("choices", [])
            if not choices:
                return ""
            message = choices[0].get("message", {})
            content = message.get("content", "")
            return str(content).strip()
        except Exception:
            return ""

    def _extract_text_from_responses(self, data: Dict) -> str:
        """Parse output text from Responses API result (Volcengine Ark format)."""
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
        Call LLM API with automatic format detection.
        Supports both OpenAI Chat Completions and Volcengine Ark formats.
        """
        if not (self.api_key and self.base_url and self.model):
            self.debug_info.append("❌ API configuration incomplete")
            return ""

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        
        # Choose the correct request format based on the service provider
        if self._is_volcengine_ark():
            # Volcengine Ark format
            url = self._responses_url()
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
            self.debug_info.append(f"🔗 Using Volcengine Ark format: {url}")
        else:
            # OpenAI standard format (DeepSeek, SiliconFlow, etc.)
            url = self._chat_completions_url()
            messages = []
            if system_prompt.strip():
                messages.append({"role": "system", "content": system_prompt.strip()})
            messages.append({"role": "user", "content": prompt})
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }
            self.debug_info.append(f"🔗 Using OpenAI standard format: {url}")
        
        self.debug_info.append(f"📤 Sending request, model: {self.model}")

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            self.debug_info.append(f"📥 Response status code: {resp.status_code}")
            
            if resp.status_code >= 300:
                self.debug_info.append(f"❌ HTTP error: {resp.status_code} - {resp.text[:300]}")
                return ""
            
            data = resp.json()
            self.debug_info.append(f"✅ Response data: {json.dumps(data, ensure_ascii=False)[:500]}...")
            
            # Choose the correct text extraction method based on format
            if self._is_volcengine_ark():
                text = self._extract_text_from_responses(data)
            else:
                text = self._extract_text_from_chat(data)
            
            self.debug_info.append(f"📝 Extracted text length: {len(text)}")
            return text
        except Exception as e:
            self.debug_info.append(f"❌ Exception: {str(e)}")
            return ""

    def _responses_url(self) -> str:
        """Resolve Ark/OpenAI-compatible responses endpoint URL (for Volcengine)."""
        base = self.base_url.rstrip("/")
        if base.endswith("/responses"):
            return base
        if base.endswith("/api/v3"):
            return f"{base}/responses"
        return f"{base}/api/v3/responses"

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
        First stage: LLM pre-analyzes retrieval results and outputs
        1) Summary
        2) Recommended interest tags (for user secondary selection)
        """
        self.debug_info = []  # Reset debug information
        
        if not items:
            return {"overview": "No information available.", "recommended_tags": []}

        refs = "\n".join(
            [
                f"[{i+1}] Title:{r.get('title', '')} | Source:{r.get('source_type', '')}/{r.get('source_name', '')} | Content:{r.get('content', '')[:180]}"
                for i, r in enumerate(items[:50])
            ]
        )

        if self.api_key and self.base_url and self.model:
            try:
                self.debug_info.append("🚀 Starting LLM pre-analysis...")
                
                system_prompt = (
                    "You are a professional information analysis assistant responsible for organizing and summarizing user-provided information content."
                    "Your task is to objectively and neutrally extract key information without any sensitive evaluations."
                    "Please strictly output in the JSON format requested by the user, without adding additional explanations."
                )
                
                prompt = (
                    f'Please analyze the following information collection around "{keyword}" and output the result in JSON format.\n\n'
                    "JSON field description:\n"
                    '- overview: High-quality English summary of the results (covering core points, concise and clear, no more than 300 words)\n'
                    f'- tags: Maximum {top_k_tags} interest tags that can be used for secondary filtering (2-8 word phrases, avoid generic words like "information/news/related")\n\n'
                    "Only output the JSON object, no explanations.\n\n"
                    f"Candidate information:\n{refs}"
                )
                self.debug_info.append(f"📝 Prompt length: {len(prompt)} characters")
                
                raw = self._call_llm_text(prompt, temperature=0.2, system_prompt=system_prompt)
                self.debug_info.append(f"📄 LLM raw return: {raw[:500] if raw else 'No return'}...")
                
                data = self._extract_json(raw, object_mode=True) or {}
                self.debug_info.append(f"🔍 Parsed JSON: {json.dumps(data, ensure_ascii=False)[:300]}...")
                
                overview = str(data.get("overview", "")).strip()
                tags = data.get("tags", [])
                tags = [str(x).strip() for x in tags if str(x).strip()]
                tags = self._clean_tags(tags, keyword)[:top_k_tags]
                
                if overview or tags:
                    self.debug_info.append(f"✅ LLM analysis successful - summary length: {len(overview)}, number of tags: {len(tags)}")
                    return {
                        "overview": (overview or "Pre-analysis completed.")[:summary_len],
                        "recommended_tags": tags[:top_k_tags],
                    }
                else:
                    self.debug_info.append("⚠️ LLM returned empty data")
            except Exception as e:
                self.debug_info.append(f"❌ LLM call exception: {str(e)}")
                pass

        # Local fallback: keyword extraction + concatenation summary
        self.debug_info.append("🔄 Using local fallback algorithm")
        tags = self.extract_focus_keywords(items, keyword, top_k=top_k_tags)
        head_titles = "; ".join([x.get("title", "") for x in items[:6]])
        overview = (
            f"A total of {len(items)} items were retrieved around '{keyword}'."
            f"Main topics include: {head_titles}."
            "It is recommended to first select a direction from the recommended tags, then view the secondary precise results."
        )
        return {"overview": overview[:summary_len], "recommended_tags": tags}

    def _clean_tags(self, tags: List[str], keyword: str) -> List[str]:
        bad = {"information", "news", "related", "trends", "content", "materials", "recommended", "platform", "search"}
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
        Extract keywords from search results that can be used for secondary filtering.
        When API is available, prioritize LLM; when API is not available, use local high-frequency word fallback.
        """
        if not items:
            return []

        if self.api_key and self.base_url and self.model:
            try:
                refs = "\n".join(
                    [f"- {r.get('title', '')} {r.get('content', '')[:120]}" for r in items[:30]]
                )
                prompt = (
                    f"Please extract {top_k} most distinctive keywords from the following information related to '{keyword}'."
                    "Output requirement: Only output a JSON array, such as [\"word1\",\"word2\"], no other text.\n"
                    f"{refs}"
                )
                raw = self._call_llm_text(prompt, temperature=0.1)
                # Try to robustly parse model output to avoid parsing failure due to additional explanatory text.
                arr = self._extract_json(raw, object_mode=False)
                if isinstance(arr, list):
                    kws = [str(x).strip() for x in arr if str(x).strip()]
                    if kws:
                        return self._clean_tags(kws, keyword)[:top_k]
                # Compatible with non-JSON output like "keyword1,keyword2"
                alt = re.split(r"[，,、\n]+", raw)
                alt = [x.strip(" -•\t\r ") for x in alt if x.strip()]
                if alt:
                    return self._clean_tags(alt, keyword)[:top_k]
            except Exception:
                pass

        # Local fallback
        import re
        from collections import Counter

        stop_words = {
            "we",
            "you",
            "they",
            "this",
            "a",
            "and",
            "conduct",
            "related",
            "information",
            "content",
            "user",
            "platform",
            "can",
            "through",
            "about",
            "how",
            "this is",
            "use",
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
        Perform semantic relevance filtering and sorting on candidate results based on LLM API.
        Return the most relevant top_n items; if the call fails, fallback to the original list.
        """
        if not items:
            return []
        if not (self.api_key and self.base_url and self.model):
            return items[:top_n]

        refs = []
        for i, row in enumerate(items[:120], start=1):
            refs.append(
                f"[{i}] Title:{row.get('title','')} | Source:{row.get('source_type','')} | Content:{row.get('content','')[:180]}"
            )
        focus = ", ".join([x for x in selected_keywords if x.strip()]) or "None"
        prompt = (
            f"Please filter the most relevant content from the candidate information.\n"
            f"User search term: {keyword}\n"
            f"User selected focus keywords: {focus}\n"
            "Task: Select the most relevant items in descending order of relevance, return a JSON array containing only numbers, for example [2,5,9].\n"
            f"Return at most {top_n} items, no explanatory text.\n\n"
            "Candidate information:\n" + "\n".join(refs)
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
            # Pure search summary mode: interest tags do not participate in grouping, only summarize by search term as a whole.
            return {"Search Term Summary": items[:80] if items else []}

        groups: Dict[str, List[Dict]] = {tag: [] for tag in tags if tag.strip()}
        groups["Free Search"] = []
        for item in items:
            text = f"{item.get('title', '')} {item.get('content', '')}".lower()
            matched = False
            for tag in list(groups.keys()):
                if tag != "Free Search" and tag.lower() in text:
                    groups[tag].append(item)
                    matched = True
            if keyword.lower() in text and not matched:
                groups["Free Search"].append(item)
        if not groups["Free Search"]:
            groups["Free Search"] = items[:20]
        return {k: v for k, v in groups.items() if v}

    def _one_tag_summary(self, rows: List[Dict], tag: str, keyword: str, summary_len: int) -> str:
        if not rows:
            return "No information available."
        prompt = self._build_prompt(rows, tag, keyword, summary_len)

        if self.api_key and self.base_url and self.model:
            try:
                text = self._call_llm_text(
                    prompt,
                    temperature=0.2,
                    system_prompt="You are a rigorous information analysis assistant, only output content related to user interests.",
                ).strip()
                if text:
                    return text[:summary_len]
            except Exception:
                pass

        # Local fallback summary to ensure Demo runs without API key
        titles = "; ".join([r.get("title", "") for r in rows[:6]])
        points = " ".join([r.get("content", "")[:50] for r in rows[:6]])
        return (
            f"Core Conclusions: Key information around '{tag}' and '{keyword}' includes: {titles}.\n"
            f"Key Developments: {points[: summary_len // 2]}\n"
            "Action Suggestions: Prioritize tracking high-frequency keywords and establish a weekly learning and review checklist based on the original text."
        )[:summary_len]

    def _build_prompt(self, rows: List[Dict], tag: str, keyword: str, summary_len: int) -> str:
        ref = "\n\n".join(
            [
                f"[{i+1}] Title:{r.get('title', '')}\nSource:{r.get('source_type', '')}/{r.get('source_name', '')}\nContent:{r.get('content', '')[:300]}"
                for i, r in enumerate(rows[:20])
            ]
        )
        return (
            f"Please generate a targeted summary around the user's search term '{keyword}' and interest tag '{tag}'.\n"
            "Requirements:\n"
            "1. Only retain relevant information, reject irrelevant content;\n"
            "2. Output structure: Core Conclusions, Key Developments, Action Suggestions;\n"
            f"3. Total word count not exceeding {summary_len} words;\n"
            "4. Cover key points and sources in the information.\n\n"
            f"Input information:\n{ref}"
        )
