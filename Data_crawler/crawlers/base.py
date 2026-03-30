from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Dict, Optional

import requests


@dataclass
class HttpConfig:
    timeout: int = 10
    max_retries: int = 3
    min_delay: float = 0.5
    max_delay: float = 2.0


class BaseCrawler:
    """
    提供基础 HTTP 请求、随机延时、失败重试等通用能力。
    所有具体站点爬虫继承该类。
    """

    def __init__(self, http_config: Optional[HttpConfig] = None) -> None:
        self.http_config = http_config or HttpConfig()
        self.session = requests.Session()
        self.session.headers.update(self.default_headers())

    @staticmethod
    def default_headers() -> Dict[str, str]:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0 Safari/537.36"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    def _sleep_random(self) -> None:
        delay = random.uniform(self.http_config.min_delay, self.http_config.max_delay)
        time.sleep(delay)

    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        简单的 GET 请求封装。
        - 自定义请求头
        - 随机延时
        - 失败重试（网络错误或 5xx）
        """
        retries = 0
        while retries < self.http_config.max_retries:
            self._sleep_random()
            try:
                resp = self.session.get(
                    url, timeout=self.http_config.timeout, **kwargs
                )
                # 5xx 时重试，4xx 直接返回
                if 500 <= resp.status_code < 600:
                    retries += 1
                    continue
                return resp
            except requests.RequestException:
                retries += 1
                continue
        return None

