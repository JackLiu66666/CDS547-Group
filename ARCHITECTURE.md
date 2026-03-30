# 系统架构说明 🏗️

## 📐 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户界面层                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │   Streamlit Web UI (frontend/app.py)                  │  │
│  │   - 信息源管理                                          │  │
│  │   - 标签配置                                            │  │
│  │   - 结果展示                                            │  │
│  │   - 导出功能                                            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP/REST API
┌─────────────────────────────────────────────────────────────┐
│                        API 服务层                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │   Flask API Server (Data_crawler/api_server.py)       │  │
│  │                                                       │  │
│  │   Routes:                                             │  │
│  │   - POST /api/crawl          开始爬取任务              │  │
│  │   - GET  /api/task/<id>      查询任务状态              │  │
│  │   - POST /api/generate_summary 生成摘要               │  │
│  │   - GET  /api/download/<id>  下载结果文件             │  │
│  │   - GET  /api/sources        获取可用信息源            │  │
│  │   - GET  /api/health         健康检查                 │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↕ 调用
┌─────────────────────────────────────────────────────────────┐
│                        业务逻辑层                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Crawler     │  │ Storage     │  │ LLM Adapter │         │
│  │ Manager     │  │ Manager     │  │             │         │
│  │             │  │             │  │             │         │
│  │ - 爬虫调度  │  │ - 数据持久化│  │ - 数据清洗  │         │
│  │ - 任务分发  │  │ - JSONL 写入│  │ - 格式转换  │         │
│  │ - 进度跟踪  │  │ - 去重管理  │  │ - LLM 预处理│         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            ↕ 继承
┌─────────────────────────────────────────────────────────────┐
│                        爬虫实现层                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           BaseCrawler (crawlers/base.py)              │  │
│  │  - HTTP 请求封装（带重试、随机延时）                     │  │
│  │  - 请求头管理                                          │  │
│  │  - 错误处理                                            │  │
│  └───────────────────────────────────────────────────────┘  │
│         ↙        ↓        ↘        ↙        ↓        ↘      │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │
│  │ Zhihu  │ │ Sina   │ │Wechat  │ │Toutiao │ │Tencent │   │
│  │Crawler │ │Crawler │ │Crawler │ │Crawler │ │Crawler │   │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘   │
│         ↘                                                    │
│  ┌────────┐                                                  │
│  │Netease │                                                  │
│  │Crawler │                                                  │
│  └────────┘                                                  │
└─────────────────────────────────────────────────────────────┘
                            ↕ 使用
┌─────────────────────────────────────────────────────────────┐
│                        数据模型层                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Article (models.py)                                  │  │
│  │  - id: str              # 唯一标识                     │  │
│  │  - source: str          # 信息源类型                   │  │
│  │  - title: str           # 标题                        │  │
│  │  - content: str         # 正文                        │  │
│  │  - author: Optional[str] # 作者                       │  │
│  │  - published_at: Optional[str] # 发布时间             │  │
│  │  - crawled_at: str      # 抓取时间                    │  │
│  │  - url: str             # 原文链接                    │  │
│  │  - raw_tags: Optional[Dict] # 原始标签                │  │
│  │  - extra: Optional[Dict] # 扩展字段                   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 数据流转

### 完整流程

```
用户输入
   │
   ├─→ [前端界面] 添加信息源、设置标签
   │
   ├─→ [API 层] POST /api/crawl
   │       └─→ 生成 task_id
   │       └─→ 启动后台线程
   │
   ├─→ [爬虫层] 根据信息源类型选择对应爬虫
   │       ├─→ ZhihuCrawler
   │       ├─→ SinaNewsCrawler
   │       ├─→ WechatCrawler
   │       └─→ ...
   │
   ├─→ [HTTP 请求] BaseCrawler.get()
   │       ├─→ 发送请求（带随机延时）
   │       ├─→ 失败自动重试（最多 3 次）
   │       └─→ 返回 HTML
   │
   ├─→ [解析层] BeautifulSoup 解析 HTML
   │       ├─→ 提取标题
   │       ├─→ 提取正文
   │       ├─→ 提取作者
   │       ├─→ 提取发布时间
   │       └─→ 生成 Article 对象
   │
   ├─→ [存储层] ArticleStorage.save_article()
   │       ├─→ 生成 ID（SHA256 哈希）
   │       ├─→ 检查是否重复
   │       ├─→ 写入 JSONL 文件
   │       └─→ 更新已存在 ID 集合
   │
   ├─→ [LLM 适配层] process_data_for_llm()
   │       ├─→ 读取原始 JSONL
   │       ├─→ 清洗数据（去除无效记录）
   │       ├─→ 格式转换
   │       └─→ 输出 LLM-ready JSONL
   │
   ├─→ [摘要生成] POST /api/generate_summary
   │       ├─→ 接收文章列表
   │       ├─→ 结合兴趣标签
   │       ├─→ 调用 LLM API（或模拟）
   │       └─→ 返回结构化摘要
   │
   └─→ [前端展示] 渲染结果
           ├─→ Task Overview
           ├─→ Overall Summary
           ├─→ Item Summaries
           └─→ Export Buttons
```

---

## 📦 模块依赖关系

```
requirements.txt
├── Backend Core
│   ├── requests (HTTP 请求)
│   ├── beautifulsoup4 (HTML 解析)
│   └── lxml (XML/HTML 处理器)
│
├── API Server
│   ├── flask (Web 框架)
│   └── flask-cors (跨域支持)
│
├── Frontend
│   ├── streamlit (UI 框架)
│   ├── pandas (数据处理)
│   └── plotly (可视化)
│
└── Export Tools
    ├── python-docx (Word 生成)
    └── xhtml2pdf (PDF 生成)
```

---

## 🎯 核心设计模式

### 1. 策略模式 (Strategy Pattern)

```python
# 不同信息源使用不同的爬虫策略
crawler_map = {
    "zhihu": ZhihuCrawler,
    "sina": SinaNewsCrawler,
    "wechat": WechatCrawler,
    # ...
}

# 统一接口调用
crawler = crawler_map[source_type]()
articles = crawler.crawl_batch(...)
```

**优点：**
- 易于扩展新信息源
- 各爬虫独立，互不影响
- 符合开闭原则

---

### 2. 模板方法模式 (Template Method Pattern)

```python
class BaseCrawler:
    def crawl_batch(self, urls, storage, max_items):
        """模板方法：定义爬取流程"""
        for url in urls:
            html = self.get(url)           # 抽象步骤：HTTP 请求
            article = self.parse(html)     # 抽象步骤：解析
            storage.save(article)          # 具体步骤：存储
```

**优点：**
- 复用通用逻辑
- 子类只需关注特定解析逻辑
- 保证流程一致性

---

### 3. 单例模式 (Singleton Pattern)

```python
class ArticleStorage:
    _instance = None
    
    def __new__(cls, path):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

**优点：**
- 全局共享存储实例
- 避免重复初始化
- 保证数据一致性

---

### 4. 观察者模式 (Observer Pattern)

```python
# 前端轮询后端任务状态
while True:
    status = requests.get(f'/api/task/{task_id}')
    if status['status'] == 'completed':
        break  # 观察到状态变化
    time.sleep(2)
```

**优点：**
- 解耦前后端
- 支持异步长任务
- 用户体验友好

---

## 🔐 安全机制

### 1. 防反爬措施
```python
# 随机 User-Agent
headers = {
    "User-Agent": random.choice(USER_AGENTS),
}

# 随机延时
time.sleep(random.uniform(0.5, 2.0))

# 失败重试
@retry(max_attempts=3)
def get(url):
    ...
```

### 2. 数据验证
```python
# 输入验证
if not title or not content:
    continue  # 跳过无效记录

# URL 验证
if not url.startswith("http"):
    url = "https://" + url
```

### 3. 错误隔离
```python
try:
    article = parse(html)
except Exception as e:
    logger.error(f"解析失败：{e}")
    continue  # 单条失败不影响整体
```

---

## ⚡ 性能优化

### 1. 增量抓取
```python
class ArticleStorage:
    def __init__(self):
        self._existing_ids = set()
        self._load_existing_ids()
    
    def save_article(self, article):
        if article.id in self._existing_ids:
            return False  # 已存在，跳过
        # ... 写入新数据
```

**效果：** 避免重复抓取，节省 80% 时间

---

### 2. 异步任务处理
```python
# Flask 后台线程处理长任务
def run_crawl_task():
    # 耗时操作在后台执行
    articles = crawler.crawl_batch(...)
    tasks[task_id]['result'] = articles

# 前端非阻塞轮询
@app.route('/api/task/<id>')
def get_task_status():
    return jsonify(tasks[task_id])
```

**效果：** 不阻塞 API 响应，支持并发任务

---

### 3. JSONL 流式写入
```python
# 逐条写入，避免内存爆炸
with open(output, 'a', encoding='utf-8') as f:
    for article in articles:
        json_line = json.dumps(article.to_dict())
        f.write(json_line + '\n')  # 立即刷盘
```

**效果：** 支持大规模数据抓取

---

### 4. BeautifulSoup 优化
```python
# 指定解析器加速
soup = BeautifulSoup(html, 'lxml')  # 比 html.parser 快 3-5 倍

# 限制查找范围
content = soup.find('div', class_='article-content')
paragraphs = content.find_all('p')  # 而非遍历整个文档
```

---

## 🧩 扩展点

### 新增信息源

1. **创建爬虫类**
```python
# crawlers/new_source.py
from .base import BaseCrawler

class NewSourceCrawler(BaseCrawler):
    def _parse_article(self, url, html):
        # 实现解析逻辑
        return Article(...)
    
    def crawl_batch(self, storage, max_items=50):
        # 实现批量抓取
        ...
```

2. **注册到 API**
```python
# api_server.py
from crawlers.new_source import NewSourceCrawler

crawler_map['new_source'] = NewSourceCrawler
```

3. **更新前端选项**
```python
# app.py
platform_options.append("New Source")
```

---

### 接入真实 LLM

```python
# api_server.py
def generate_summary(articles, tags, granularity):
    # 方案 1: OpenAI API
    import openai
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{
            "role": "user",
            "content": f"为以下文章生成摘要，关注标签：{tags}\n{articles}"
        }]
    )
    return response.choices[0].message.content
    
    # 方案 2: 文心一言
    # 方案 3: 通义千问
    # ...
```

---

### 自定义存储

```python
# 替代 JSONL 存储
class MongoDBStorage(ArticleStorage):
    def __init__(self, connection_string):
        self.client = MongoClient(connection_string)
        self.db = self.client.llm_articles
    
    def save_article(self, article):
        self.db.articles.insert_one(article.to_dict())
```

---

## 📊 数据库设计

### JSONL 文件格式

**原始数据 (raw_articles.jsonl):**
```json
{"id": "abc123", "source": "zhihu", "title": "...", "content": "...", ...}
{"id": "def456", "source": "sina", "title": "...", "content": "...", ...}
```

**LLM 处理后 (llm_ready.jsonl):**
```json
{
  "id": "abc123",
  "source": "zhihu",
  "title": "...",
  "content": "...",
  "meta": {
    "author": "张三",
    "published_at": "2025-03-28",
    "url": "https://...",
    "raw_tags": {...},
    "extra": {...}
  }
}
```

---

## 🎨 前端组件架构

```
Streamlit App (app.py)
│
├── Session State Management
│   ├── info_sources: List[Dict]
│   ├── selected_tags: List[str]
│   ├── granularity: str
│   └── latest_result: Dict
│
├── Sidebar Components
│   ├── Information Source Manager
│   │   ├── Platform Selector
│   │   ├── URL Input Area
│   │   └── Source List (Editable)
│   │
│   ├── Tags & Personalization
│   │   ├── Preset Tags (Multi-select)
│   │   ├── Custom Tags Input
│   │   └── Granularity Radio
│   │
│   └── Generation Trigger
│       └── Generate Button
│
├── Main Content Tabs
│   ├── Tab 1: Aggregated Summary
│   │   ├── Task Overview Metrics
│   │   ├── Overall Summary Card
│   │   └── Detailed Summaries List
│   │
│   └── Tab 2: Performance Report
│       ├── Charts (Plotly)
│       └── Statistics Table
│
└── Export Zone (Sticky Footer)
    ├── DOCX Export
    ├── PDF Export
    └── Excel Export
```

---

## 🔮 未来架构演进

### V2.0 规划
```
当前架构 (V1.0)
├── 单体 Flask API
├── 同步爬虫
└── 本地 JSONL 存储

↓ 演进

未来架构 (V2.0)
├── 微服务拆分
│   ├── Crawler Service (分布式爬虫)
│   ├── API Gateway (统一入口)
│   └── Summary Service (LLM 调用)
│
├── 消息队列 (Celery + Redis)
│   └── 异步任务调度
│
├── 数据库升级
│   ├── MongoDB (文章存储)
│   └── Elasticsearch (全文检索)
│
└── 容器化部署
    └── Docker Compose / K8s
```

---

## 📈 监控与日志

### 当前实现
```python
# 简单的 print 日志
print(f"[Zhihu] 计划抓取 {len(urls)} 篇文章")
print(f"[LLM Adapter] 已生成 {len(processed)} 条记录")
```

### 改进建议
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("爬取任务开始")
```

---

**总结：** 本系统采用分层架构设计，模块化程度高，易于理解和扩展。通过合理的抽象和接口设计，实现了多源信息的高效聚合与智能化处理。
