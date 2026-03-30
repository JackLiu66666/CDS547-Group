### 项目简介

这是一个**多信息源文章爬虫 + LLM 预处理**的小工具，目前支持三类主流信息源：

- **知乎专栏文章**：通过提供 `zhuanlan.zhihu.com` 文章链接列表抓取完整正文
- **新浪新闻**：通过新浪公开滚动新闻接口抓取列表，再进入新闻详情页解析完整正文
- **微信公众号公开文章**：通过 `mp.weixin.qq.com` 的公开文章链接抓取完整正文

所有信息源抓取结果都会统一标准化为相同字段，为后续用 LLM 做筛选 / 总结 / 标注提供基础数据。

---

### 标准化字段定义

内部使用的核心数据结构为 `Article`（见 `models.py`），字段包括：

- **id**：唯一标识（当前实现为 URL 的短哈希）
- **source**：信息源标识，例如 `zhihu` / `sina_news` / `wechat`
- **title**：标题
- **content**：完整正文内容（为 LLM 设计，尽量保证干净和完整）
- **author**：作者（可能为空）
- **published_at**：发布时间（ISO8601 字符串，可能为空）
- **crawled_at**：抓取时间（ISO8601 字符串）
- **url**：原文链接
- **raw_tags**：原始标签或话题（来源站点的原始字段，结构不做强限制）
- **extra**：预留扩展字段（可存放原始 JSON、频道信息等）

所有信息源的抓取逻辑，最终都要转换为该结构并写入本地存储。

---

### 数据存储与增量抓取

- **存储格式**：`data/raw_articles.jsonl`（JSON Lines，每行一条 `Article`）
- **增量策略**：
  - 启动时会扫描已有文件，建立已抓取 `id` 集合
  - 新文章若 `id` 已存在则自动跳过，避免重复抓取
  - 每抓取一篇文章立即追加写入，程序中途崩溃时已抓取的数据不会丢失

LLM 预处理结果会写入：

- **`data/llm_ready.jsonl`**：结构更适合直接送入 LLM 的简化版数据（含 `title`、`content` 和 `meta`）

---

### 反爬基础策略

- **自定义请求头**：统一设置合理的 `User-Agent` 和 `Accept-Language`
- **随机延时**：每次 HTTP 请求前随机 `0.5–2.0s` 延时，避免高频访问
- **失败重试**：
  - 网络错误或服务器 `5xx` 时自动重试（默认最多 3 次）
  - `4xx` 认为是客户端问题，不再重试
- **安全边界**：
  - 仅抓取平台**公开内容**（知乎专栏公开文章、新浪公开新闻、公众号公开链接）
  - 不尝试绕过登录、验证码等安全机制
  - 默认不处理 robots.txt，如需严格合规，请在部署前自行检查各站点的 robots 规则

---

### 命令行用法

在项目根目录执行：

```bash
python main.py \
  --sources zhihu sina wechat \
  --max-items 30 \
  --start-date 2025-01-01 \
  --end-date 2025-01-31 \
  --zhihu-url-file configs/zhihu_urls.txt \
  --wechat-url-file configs/wechat_urls.txt
```

#### 核心参数说明

- **`--sources`**：选择要抓取的信息源，可多选，取值范围：
  - `zhihu`：知乎专栏文章
  - `sina`：新浪新闻
  - `wechat`：微信公众号公开文章
- **`--max-items`**：每个信息源**最多**抓取多少篇文章
- **`--start-date` / `--end-date`**：
  - 发布时间范围过滤，格式 `YYYY-MM-DD`
  - 目前主要对新浪新闻生效（新浪接口自带时间字段）
- **`--zhihu-url-file`**：
  - 文本文件，每行一个知乎专栏文章 URL，例如：
    - `https://zhuanlan.zhihu.com/p/1234567890`
  - 用于精确控制要抓取的知乎文章集合
- **`--wechat-url-file`**：
  - 文本文件，每行一个公众号公开文章 URL，例如：
    - `https://mp.weixin.qq.com/s/xxxxxxxx`
- **`--output`**：原始抓取结果文件路径（默认 `data/raw_articles.jsonl`）
- **`--skip-llm`**：如果指定，则只抓取数据，不生成 LLM 预处理文件

---

### 单源 / 多源抓取示例

- **仅抓取新浪新闻（最近若干条）**：

```bash
python main.py --sources sina --max-items 100
```

- **只抓取指定的知乎专栏文章**：

```bash
python main.py \
  --sources zhihu \
  --zhihu-url-file configs/zhihu_urls.txt \
  --max-items 50
```

- **抓取公众号公开文章，并跳过 LLM 预处理**：

```bash
python main.py \
  --sources wechat \
  --wechat-url-file configs/wechat_urls.txt \
  --max-items 20 \
  --skip-llm
```

---

### 与 LLM 的衔接

`llm_adapter.py` 会读取 `data/raw_articles.jsonl`，做轻量清洗与字段整理后输出：

- **`data/llm_ready.jsonl`**：每行一个 JSON 对象，包含：
  - `id` / `source` / `title` / `content`
  - `meta`：作者、发布时间、抓取时间、原文链接、原始标签等

你可以：

- 直接把 `content` 作为 LLM 的上下文（例如做筛选、聚类、摘要）
- 先用额外脚本对 `llm_ready.jsonl` 做过滤（按源、时间、关键词等）
- 再批量喂入 LLM，生成更高层的结构化标注

---

### 后续可扩展方向

- 新增信息源：例如学术论文（arXiv 等）、更多新闻站、知乎问答等
- 增强时间范围控制：为知乎 / 公众号增加基于发布时间的过滤逻辑
- 引入数据库：将 JSONL 替换为 SQLite / PostgreSQL，方便复杂查询
- 更智能的反爬策略：如代理池、请求节流、失败统计等（需遵守各站点使用条款）

