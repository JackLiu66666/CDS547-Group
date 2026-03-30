# config.py
import time
import os

# 1. 自定义请求头（模拟正常浏览器访问，降低反爬风险）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive"
}

# 2. 爬虫参数配置
CRAWL_PARAMS = {
    "retry_times": 2,  # 失败重试次数
    "delay_min": 1,    # 最小延时（秒）
    "delay_max": 3,    # 最大延时（秒）
    "batch_num": 10    # 为了快速测试，单源批量抓取数量先设为10（后续可自行改为50或更多）
}

# 3. 存储路径配置（自动创建 data 和 log 目录）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "crawl_data")
LOG_DIR = os.path.join(BASE_DIR, "crawl_log")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# 4. 信息源标识
SOURCE_MAP = {
    "zhihu": "知乎",
    "sina_news": "新浪新闻",
    "wechat": "微信公众号",
    "toutiao": "今日头条",
    "tencent_news": "腾讯新闻",
    "netease_news": "网易新闻"
}

# 5. 当前日期（用于文件按天命名）
CUR_DATE = time.strftime("%Y%m%d", time.localtime())