# utils.py
import time
import random
import hashlib
import logging
import os
from config import LOG_DIR, CUR_DATE


# 1. 生成唯一ID（基于URL+时间，用于LLM端去重）
def generate_unique_id(url):
    timestamp = str(int(time.time() * 1000))
    md5 = hashlib.md5()
    md5.update((url + timestamp).encode("utf-8"))
    return md5.hexdigest()


# 2. 随机延时（防反爬）
def random_delay(delay_min, delay_max):
    delay = random.uniform(delay_min, delay_max)
    time.sleep(delay)


# 3. 日志初始化（文件+控制台双输出）
def init_logger(source):
    log_file = os.path.join(LOG_DIR, f"{source}_{CUR_DATE}.log")
    log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    logger = logging.getLogger(source)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(log_format)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger


# 4. 失败重试装饰器
def retry(retry_times):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(retry_times + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger = args[0].logger if hasattr(args[0], 'logger') else logging.getLogger(__name__)
                    if i < retry_times:
                        logger.warning(f"抓取失败，第{i + 1}次重试，原因：{str(e)[:50]}")
                        random_delay(1, 2)
                        continue
                    else:
                        logger.error(f"抓取失败，已重试{retry_times}次，原因：{str(e)[:50]}")
                        return None

        return wrapper

    return decorator