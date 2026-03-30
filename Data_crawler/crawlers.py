# crawlers.py
import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import os
from config import HEADERS, CRAWL_PARAMS, DATA_DIR, SOURCE_MAP, CUR_DATE
from utils import generate_unique_id, random_delay, init_logger, retry


class ZhihuCrawler:
    def __init__(self):
        self.source = "zhihu"
        self.source_cn = SOURCE_MAP[self.source]
        self.logger = init_logger(self.source)
        self.batch_num = CRAWL_PARAMS["batch_num"]
        self.api_url = "https://www.zhihu.com/api/v4/columns/c_1289328370/items"  # 知乎公开专栏API

    @retry(CRAWL_PARAMS["retry_times"])
    def crawl_single_page(self, offset=0):
        params = {"limit": 20, "offset": offset}
        response = requests.get(self.api_url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()

        items = response.json().get("data", [])
        crawl_data = []
        for item in items:
            unique_id = generate_unique_id(item.get("url", ""))
            crawl_data.append({
                "unique_id": unique_id,
                "source": self.source_cn,
                "title": item.get("title", "未知"),
                "content": item.get("excerpt", "未知").replace("\n", ""),
                "author": item.get("author", {}).get("name", "未知"),
                "publish_time": item.get("created_time", "未知"),
                "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "url": item.get("url", "未知"),
                "tags": "科技,知乎"
            })
            self.logger.info(f"【{self.source_cn}】抓取成功: {item.get('title', '未知')[:15]}...")
        random_delay(CRAWL_PARAMS["delay_min"], CRAWL_PARAMS["delay_max"])
        return crawl_data

    def crawl_batch(self):
        self.logger.info(f"开始抓取 {self.source_cn}...")
        all_data, offset = [], 0
        while len(all_data) < self.batch_num:
            page_data = self.crawl_single_page(offset)
            if not page_data: break
            all_data.extend(page_data)
            offset += 20
        all_data = all_data[:self.batch_num]
        self.save_data(all_data)
        return all_data

    def save_data(self, data):
        if not data: return
        df = pd.DataFrame(data)
        file_path = os.path.join(DATA_DIR, f"{self.source}_{CUR_DATE}.csv")
        df.to_csv(file_path, mode="a", header=not os.path.exists(file_path), index=False, encoding="utf-8-sig")


class SinaNewsCrawler:
    def __init__(self):
        self.source = "sina_news"
        self.source_cn = SOURCE_MAP[self.source]
        self.logger = init_logger(self.source)
        self.batch_num = CRAWL_PARAMS["batch_num"]
        self.list_url = "https://tech.sina.com.cn/internet/"

    @retry(CRAWL_PARAMS["retry_times"])
    def crawl_single_news(self, news_url):
        response = requests.get(news_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "lxml")

        title = soup.find("h1", class_="main-title")
        author = soup.find("span", class_="source")
        content_list = soup.find_all("p", class_="article-content")

        title_text = title.get_text(strip=True) if title else "未知"
        content_text = "".join([p.get_text(strip=True) for p in content_list]) if content_list else "未知"

        news_data = {
            "unique_id": generate_unique_id(news_url),
            "source": self.source_cn,
            "title": title_text,
            "content": content_text,
            "author": author.get_text(strip=True) if author else "未知",
            "publish_time": "未知",
            "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "url": news_url,
            "tags": "科技,新浪新闻"
        }
        self.logger.info(f"【{self.source_cn}】抓取成功: {title_text[:15]}...")
        random_delay(CRAWL_PARAMS["delay_min"], CRAWL_PARAMS["delay_max"])
        return news_data

    def crawl_batch(self):
        self.logger.info(f"开始抓取 {self.source_cn}...")
        response = requests.get(self.list_url, headers=HEADERS, timeout=10)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "lxml")

        news_urls = list(set([a.get("href") for a in soup.find_all("a") if a.get("href") and "doc-" in a.get("href")]))
        all_data = []
        for url in news_urls[:self.batch_num]:
            data = self.crawl_single_news(url)
            if data: all_data.append(data)

        self.save_data(all_data)
        return all_data

    def save_data(self, data):
        if not data: return
        df = pd.DataFrame(data)
        file_path = os.path.join(DATA_DIR, f"{self.source}_{CUR_DATE}.csv")
        df.to_csv(file_path, mode="a", header=not os.path.exists(file_path), index=False, encoding="utf-8-sig")


class WechatCrawler:
    # 微信公众号因反爬极其严重，此处提供骨架。
    # 实际运行中，如果传入无效链接会触发重试并最终跳过，不会导致程序崩溃。
    def __init__(self):
        self.source = "wechat"
        self.source_cn = SOURCE_MAP[self.source]
        self.logger = init_logger(self.source)
        self.batch_num = CRAWL_PARAMS["batch_num"]

    @retry(CRAWL_PARAMS["retry_times"])
    def crawl_single_article(self, art_url):
        headers = HEADERS.copy()
        headers["Referer"] = "https://weixin.sogou.com/"
        response = requests.get(art_url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        title = soup.find("h2", class_="rich_media_title")
        content_list = soup.find_all("div", class_="rich_media_content")
        title_text = title.get_text(strip=True) if title else "未知"

        art_data = {
            "unique_id": generate_unique_id(art_url),
            "source": self.source_cn,
            "title": title_text,
            "content": "".join([div.get_text(strip=True) for div in content_list]) if content_list else "未知",
            "author": "未知",
            "publish_time": "未知",
            "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "url": art_url,
            "tags": "微信公众号"
        }
        self.logger.info(f"【{self.source_cn}】抓取成功: {title_text[:15]}...")
        random_delay(2, 4)
        return art_data

    def crawl_batch(self, wechat_urls):
        self.logger.info(f"开始抓取 {self.source_cn}...")
        all_data = []
        for url in wechat_urls[:self.batch_num]:
            data = self.crawl_single_article(url)
            if data: all_data.append(data)
        self.save_data(all_data)
        return all_data

    def save_data(self, data):
        if not data: return
        df = pd.DataFrame(data)
        file_path = os.path.join(DATA_DIR, f"{self.source}_{CUR_DATE}.csv")
        df.to_csv(file_path, mode="a", header=not os.path.exists(file_path), index=False, encoding="utf-8-sig")


class ToutiaoCrawler:
    def __init__(self):
        self.source = "toutiao"
        self.source_cn = SOURCE_MAP[self.source]
        self.logger = init_logger(self.source)
        self.batch_num = CRAWL_PARAMS["batch_num"]
        self.list_url = "https://www.toutiao.com/ch/news_hot/"

    @retry(CRAWL_PARAMS["retry_times"])
    def crawl_single_news(self, news_url):
        response = requests.get(news_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "lxml")

        title = soup.find("h1", class_="article-title")
        author = soup.find("div", class_="article-meta")
        content_list = soup.find_all("p")

        title_text = title.get_text(strip=True) if title else "未知"
        content_text = "".join([p.get_text(strip=True) for p in content_list if p.get_text(strip=True)]) if content_list else "未知"

        news_data = {
            "unique_id": generate_unique_id(news_url),
            "source": self.source_cn,
            "title": title_text,
            "content": content_text,
            "author": author.get_text(strip=True) if author else "未知",
            "publish_time": "未知",
            "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "url": news_url,
            "tags": "今日头条"
        }
        self.logger.info(f"【{self.source_cn}】抓取成功: {title_text[:15]}...")
        random_delay(CRAWL_PARAMS["delay_min"], CRAWL_PARAMS["delay_max"])
        return news_data

    def crawl_batch(self):
        self.logger.info(f"开始抓取 {self.source_cn}...")
        response = requests.get(self.list_url, headers=HEADERS, timeout=10)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "lxml")

        # 提取新闻链接
        news_urls = []
        for a in soup.find_all("a"):
            href = a.get("href")
            if href and "toutiao.com/a" in href:
                # 确保链接是完整的
                if not href.startswith("http"):
                    href = "https://www.toutiao.com" + href
                news_urls.append(href)
        
        # 去重
        news_urls = list(set(news_urls))
        all_data = []
        for url in news_urls[:self.batch_num]:
            try:
                data = self.crawl_single_news(url)
                if data: all_data.append(data)
            except Exception as e:
                self.logger.error(f"抓取 {url} 失败: {str(e)}")
                random_delay(CRAWL_PARAMS["delay_min"], CRAWL_PARAMS["delay_max"])

        self.save_data(all_data)
        return all_data

    def save_data(self, data):
        if not data: return
        df = pd.DataFrame(data)
        file_path = os.path.join(DATA_DIR, f"{self.source}_{CUR_DATE}.csv")
        df.to_csv(file_path, mode="a", header=not os.path.exists(file_path), index=False, encoding="utf-8-sig")


class TencentNewsCrawler:
    def __init__(self):
        self.source = "tencent_news"
        self.source_cn = SOURCE_MAP[self.source]
        self.logger = init_logger(self.source)
        self.batch_num = CRAWL_PARAMS["batch_num"]
        self.list_url = "https://news.qq.com/"

    @retry(CRAWL_PARAMS["retry_times"])
    def crawl_single_news(self, news_url):
        response = requests.get(news_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "lxml")

        title = soup.find("h1", class_="article-title")
        author = soup.find("span", class_="article-source")
        content_list = soup.find_all("p", class_="one-p")

        title_text = title.get_text(strip=True) if title else "未知"
        content_text = "".join([p.get_text(strip=True) for p in content_list]) if content_list else "未知"

        news_data = {
            "unique_id": generate_unique_id(news_url),
            "source": self.source_cn,
            "title": title_text,
            "content": content_text,
            "author": author.get_text(strip=True) if author else "未知",
            "publish_time": "未知",
            "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "url": news_url,
            "tags": "腾讯新闻"
        }
        self.logger.info(f"【{self.source_cn}】抓取成功: {title_text[:15]}...")
        random_delay(CRAWL_PARAMS["delay_min"], CRAWL_PARAMS["delay_max"])
        return news_data

    def crawl_batch(self):
        self.logger.info(f"开始抓取 {self.source_cn}...")
        response = requests.get(self.list_url, headers=HEADERS, timeout=10)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "lxml")

        # 提取新闻链接
        news_urls = []
        for a in soup.find_all("a"):
            href = a.get("href")
            if href and "news.qq.com/a/" in href:
                news_urls.append(href)
        
        # 去重
        news_urls = list(set(news_urls))
        all_data = []
        for url in news_urls[:self.batch_num]:
            try:
                data = self.crawl_single_news(url)
                if data: all_data.append(data)
            except Exception as e:
                self.logger.error(f"抓取 {url} 失败: {str(e)}")
                random_delay(CRAWL_PARAMS["delay_min"], CRAWL_PARAMS["delay_max"])

        self.save_data(all_data)
        return all_data

    def save_data(self, data):
        if not data: return
        df = pd.DataFrame(data)
        file_path = os.path.join(DATA_DIR, f"{self.source}_{CUR_DATE}.csv")
        df.to_csv(file_path, mode="a", header=not os.path.exists(file_path), index=False, encoding="utf-8-sig")


class NeteaseNewsCrawler:
    def __init__(self):
        self.source = "netease_news"
        self.source_cn = SOURCE_MAP[self.source]
        self.logger = init_logger(self.source)
        self.batch_num = CRAWL_PARAMS["batch_num"]
        self.list_url = "https://news.163.com/"

    @retry(CRAWL_PARAMS["retry_times"])
    def crawl_single_news(self, news_url):
        response = requests.get(news_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "lxml")

        title = soup.find("h1", class_="post_title")
        author = soup.find("div", class_="post_info")
        content_list = soup.find_all("p", class_="post_text")

        title_text = title.get_text(strip=True) if title else "未知"
        content_text = "".join([p.get_text(strip=True) for p in content_list]) if content_list else "未知"

        news_data = {
            "unique_id": generate_unique_id(news_url),
            "source": self.source_cn,
            "title": title_text,
            "content": content_text,
            "author": author.get_text(strip=True) if author else "未知",
            "publish_time": "未知",
            "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "url": news_url,
            "tags": "网易新闻"
        }
        self.logger.info(f"【{self.source_cn}】抓取成功: {title_text[:15]}...")
        random_delay(CRAWL_PARAMS["delay_min"], CRAWL_PARAMS["delay_max"])
        return news_data

    def crawl_batch(self):
        self.logger.info(f"开始抓取 {self.source_cn}...")
        response = requests.get(self.list_url, headers=HEADERS, timeout=10)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "lxml")

        # 提取新闻链接
        news_urls = []
        for a in soup.find_all("a"):
            href = a.get("href")
            if href and "163.com/" in href and ".html" in href:
                news_urls.append(href)
        
        # 去重
        news_urls = list(set(news_urls))
        all_data = []
        for url in news_urls[:self.batch_num]:
            try:
                data = self.crawl_single_news(url)
                if data: all_data.append(data)
            except Exception as e:
                self.logger.error(f"抓取 {url} 失败: {str(e)}")
                random_delay(CRAWL_PARAMS["delay_min"], CRAWL_PARAMS["delay_max"])

        self.save_data(all_data)
        return all_data

    def save_data(self, data):
        if not data: return
        df = pd.DataFrame(data)
        file_path = os.path.join(DATA_DIR, f"{self.source}_{CUR_DATE}.csv")
        df.to_csv(file_path, mode="a", header=not os.path.exists(file_path), index=False, encoding="utf-8-sig")