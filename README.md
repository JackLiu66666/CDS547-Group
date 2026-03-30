# LLM-Assisted Cross-Platform Information Aggregation & Personalized Summarization Tool
## LLM 辅助跨平台信息聚合与个性化摘要工具

一个强大的多源信息聚合系统，支持从知乎、微信公众号、新浪新闻、今日头条、腾讯新闻、网易新闻等平台自动抓取内容，并根据用户兴趣标签生成个性化摘要。

---

## 🌟 核心特性

### 后端特性
- ✅ **6 大信息源支持** - 知乎、微信公众号、新浪、今日头条、腾讯新闻、网易新闻
- ✅ **智能去重** - 基于 SHA256 哈希的 URL 去重机制
- ✅ **增量抓取** - 自动跳过已抓取内容
- ✅ **容错机制** - 失败重试、随机延时防反爬
- ✅ **RESTful API** - 完整的 HTTP API 接口
- ✅ **LLM 数据预处理** - 自动生成适合 LLM 处理的 JSON 格式

### 前端特性
- ✅ **现代化 UI** - Streamlit 构建的科技主题界面
- ✅ **可视化进度** - 实时显示爬取进度
- ✅ **多标签管理** - 支持预设标签和自定义标签
- ✅ **粒度控制** - 简洁/标准/详细三种摘要长度
- ✅ **关键词高亮** - 自动标记关键信息
- ✅ **导出功能** - 支持 Word、PDF、Excel 格式导出
- ✅ **历史记录** - 保存最近 3 次生成结果

---

## 🚀 快速开始

### 方法一：一键启动（推荐）

**Windows 用户：**
```bash
# 双击运行
start.bat
```

或命令行执行：
```bash
.\start.bat
```

### 方法二：手动启动

#### 1. 安装依赖
```bash
pip install -r requirements.txt
```

#### 2. 启动后端 API 服务
```bash
cd Data_crawler
python api_server.py
```
后端将在 `http://localhost:5000` 启动

#### 3. 启动前端界面（新开终端）
```bash
cd frontend
streamlit run app.py --server.port 8501
```
前端将在 `http://localhost:8501` 启动

#### 4. 访问应用
浏览器打开：**http://localhost:8501**

---

## 📖 使用指南

### 三步生成摘要

#### 第一步：添加信息源
在左侧边栏的「Information Source Management」中：
1. 选择平台类型（Zhihu / WeChat / Academic Paper / Comprehensive News）
2. 批量输入信息源（每行一个）：
   - **知乎**：专栏文章链接或搜索关键词
   - **微信公众号**：公开文章链接
   - **学术论文**：DOI 或标题/关键词
   - **综合新闻**：新闻文章链接
3. 点击「Add Sources」按钮

**示例输入：**
```
https://zhuanlan.zhihu.com/p/123456789
https://mp.weixin.qq.com/s/abcdefg
AI 最新研究进展
考研复习经验
```

最多可添加 **20** 条信息源，支持编辑和删除单条记录。

---

#### 第二步：设置兴趣标签
在「Interest Tags & Personalization」中：
1. **选择预设标签**（可多选）：
   - Latest AI Research（AI 最新研究）
   - Grad Exam Prep Tips（考研经验）
   - Career Skill Improvement（职业技能提升）
   - Hot News（热点新闻）
   - Financial Trends（金融趋势）

2. **自定义标签**（可选）：
   输入框中输入，多个标签用逗号分隔
   ```
   时间管理，英语写作，行业趋势
   ```

3. **设置摘要粒度**：
   - Concise (<300 words) - 简洁版
   - Standard (500-800 words) - 标准版（默认）
   - Detailed (>1000 words) - 详细版

4. **关键词高亮**（可选）：开启后自动标记关键信息

---

#### 第三步：生成摘要
点击「Generate Aggregated Summary」按钮

系统将自动执行：
1. **爬取阶段** - 从各平台抓取内容（约 30-60 秒）
2. **处理阶段** - 清洗和结构化数据
3. **生成阶段** - 生成个性化摘要

---

### 查看结果

生成完成后，主界面显示：

#### Tab 1: Aggregated Summary Display
- **Task Overview** - 任务统计（总数/成功/失败/成功率）
- **Overall Summary** - 综合摘要
- **Detailed Summaries** - 各来源的详细摘要（含标题、链接、作者等）

#### Tab 2: Project Results & Performance Report
- 性能指标
- 数据可视化图表

---

### 导出结果

在底部「Export Zone」区域：
1. 选择导出格式：Word / PDF / Excel
2. 点击对应格式按钮
3. 文件自动下载

---

## 🔧 高级用法

### 纯命令行模式（不经过前端）

适用于批量处理和自动化：

```bash
cd Data_crawler

# 基础用法
python main.py --sources zhihu sina wechat --max-items 50

# 指定 URL 文件
python main.py \
  --sources zhihu \
  --zhihu-url-file zhihu_urls.txt \
  --max-items 100

# 日期范围过滤（仅新浪新闻）
python main.py \
  --sources sina \
  --start-date 2025-01-01 \
  --end-date 2025-03-30 \
  --max-items 200

# 跳过 LLM 处理
python main.py --skip-llm --output custom_output.jsonl
```

**URL 文件格式：**
```txt
# zhihu_urls.txt
https://zhuanlan.zhihu.com/p/123456
https://zhuanlan.zhihu.com/p/789012

# wechat_urls.txt
https://mp.weixin.qq.com/s/abc123
https://mp.weixin.qq.com/s/def456
```

---

## 🛠️ API 接口文档

### 健康检查
```http
GET /api/health
```

响应：
```json
{
  "status": "healthy",
  "timestamp": "2025-03-30T12:00:00",
  "service": "LLM Information Aggregation API"
}
```

---

### 开始爬取
```http
POST /api/crawl
Content-Type: application/json

{
  "sources": [
    {
      "type": "zhihu",
      "urls": ["https://zhuanlan.zhihu.com/p/123"]
    },
    {
      "type": "sina",
      "max_items": 50,
      "start_date": "2025-01-01",
      "end_date": "2025-03-30"
    }
  ],
  "max_items_per_source": 50,
  "skip_llm": false
}
```

响应：
```json
{
  "task_id": "uuid-here",
  "status": "processing",
  "message": "Crawl task started successfully"
}
```

---

### 查询任务状态
```http
GET /api/task/<task_id>
```

响应：
```json
{
  "task_id": "uuid-here",
  "status": "completed",
  "progress": 100,
  "created_at": "2025-03-30T12:00:00",
  "error": null,
  "result": {
    "articles": [...],
    "llm_processed": [...],
    "total_count": 25
  }
}
```

---

### 下载结果文件
```http
GET /api/download/<task_id>/raw     # 原始数据
GET /api/download/<task_id>/llm     # LLM 处理后数据
```

---

### 生成摘要
```http
POST /api/generate_summary
Content-Type: application/json

{
  "articles": [...],
  "interest_tags": ["AI Research", "Career Development"],
  "granularity": "Standard (500-800 words)"
}
```

---

### 获取可用信息源
```http
GET /api/sources
```

---

## 📁 项目结构

```
Group/
├── Data_crawler/              # 后端爬虫模块
│   ├── api_server.py         # ✨ 新增：Flask API 服务
│   ├── main.py               # 命令行入口
│   ├── crawlers/             # 爬虫实现
│   │   ├── base.py          # 基类
│   │   ├── zhihu.py         # 知乎爬虫
│   │   ├── sina_news.py     # 新浪新闻爬虫
│   │   ├── wechat.py        # 微信公众号爬虫
│   │   ├── toutiao.py       # 今日头条爬虫
│   │   ├── tencent_news.py  # 腾讯新闻爬虫
│   │   └── netease_news.py  # 网易新闻爬虫
│   ├── models.py            # 数据模型
│   ├── storage.py           # 数据存储
│   └── llm_adapter.py       # LLM 数据预处理
├── frontend/                 # 前端 Streamlit 应用
│   ├── app.py               # ✨ 修改：集成真实 API
│   └── run_app.py           # 启动脚本
├── requirements.txt         # Python 依赖
├── start.bat               # ✨ 新增：一键启动脚本
└── README.md               # 本文档
```

---

## 💻 技术栈

### 后端
- **Python 3.8+**
- **Flask** - Web API 框架
- **Requests** - HTTP 请求库
- **BeautifulSoup4** - HTML 解析
- **lxml** - XML/HTML 处理器

### 前端
- **Streamlit** - 交互式 Web 应用框架
- **Pandas** - 数据处理
- **Plotly** - 数据可视化
- **python-docx** - Word 文档生成
- **xhtml2pdf** - PDF 生成

---

## ⚙️ 配置说明

### config.py 配置项

```python
# 请求头配置（降低反爬风险）
HEADERS = {
    "User-Agent": "Mozilla/5.0 ...",
    "Accept": "text/html,...",
    "Accept-Language": "zh-CN,zh;q=0.9"
}

# 爬虫参数
CRAWL_PARAMS = {
    "retry_times": 2,        # 失败重试次数
    "delay_min": 1,          # 最小延时（秒）
    "delay_max": 3,          # 最大延时（秒）
    "batch_num": 10          # 批量抓取数量
}

# 存储路径
DATA_DIR = "crawl_data"
LOG_DIR = "crawl_log"
```

---

## 🎯 最佳实践

### 1. 高效抓取建议
- **优先使用 URL** - 比关键词搜索更精确
- **合理设置数量** - 每个源 10-50 篇为宜
- **日期范围过滤** - 新浪新闻支持按时间筛选
- **错峰抓取** - 避免高峰时段大量请求

### 2. 标签优化
- **精准标签** - 选择 2-5 个核心标签
- **组合使用** - 预设标签 + 自定义标签
- **具体化** - 避免过于宽泛的标签

### 3. 摘要质量提升
- **高质量输入** - 确保信息来源可靠
- **适度数量** - 10-30 篇文章效果最佳
- **明确粒度** - 根据用途选择合适长度

---

## 🐛 故障排查

### 问题 1：后端 API 无法连接
**症状：** 前端提示「网络错误」或「API 调用失败」

**解决：**
```bash
# 检查后端是否启动
curl http://localhost:5000/api/health

# 手动启动后端
cd Data_crawler
python api_server.py
```

---

### 问题 2：爬取失败
**症状：** 显示「Network timeout」或「failed」

**可能原因：**
- 网络连接不稳定
- 目标网站反爬限制
- URL 失效

**解决方法：**
1. 检查网络连接
2. 减少并发数量
3. 更换有效 URL
4. 稍后重试

---

### 问题 3：依赖安装失败
**症状：** `pip install` 报错

**解决：**
```bash
# 升级 pip
python -m pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 逐个安装（排查问题包）
pip install requests beautifulsoup4 flask flask-cors streamlit
```

---

### 问题 4：端口被占用
**症状：** 「Address already in use」

**解决：**
```bash
# Windows 查看占用端口的进程
netstat -ano | findstr :5000
netstat -ano | findstr :8501

# 杀死进程（替换 PID）
taskkill /F /PID <PID>

# 或修改端口
streamlit run app.py --server.port 8502
```

---

## 📝 注意事项

1. **合法合规使用**
   - 遵守目标网站的 robots.txt
   - 不要大规模高频抓取
   - 仅用于学习研究目的

2. **版权保护**
   - 尊重原创内容版权
   - 不得用于商业目的
   - 注明信息来源

3. **隐私保护**
   - 不抓取个人隐私信息
   - 不传播敏感内容

4. **资源限制**
   - 单次最多 20 个信息源
   - 每源默认最多 50 篇文章
   - 建议按需调整参数

---

## 🎓 适用场景

### 学术研究
- 文献综述资料收集
- 研究热点追踪
- 学术会议动态

### 学习提升
- 考试备考经验收集
- 学习方法整理
- 技能提升资料

### 职业发展
- 行业动态跟踪
- 职业技能学习
- 职场经验分享

### 生活娱乐
- 旅游攻略整理
- 美食探店汇总
- 影评书评收集

---

## 📊 演示案例

### 案例 1：AI 研究进展追踪
**信息源：**
- 知乎：AI 领域专家专栏
- 微信公众号：机器之心、AI 科技评论
- 学术平台：arXiv 最新论文

**标签：** Latest AI Research, LLM, Computer Vision

**输出：** 500-800 字标准摘要，包含本周重要突破

---

### 案例 2：考研复试准备
**信息源：**
- 知乎：高分上岸经验分享
- 微信公众号：考研真题解析
- 论坛：复试面试技巧

**标签：** Grad Exam Prep Tips, Interview Skills

**输出：** 简洁版摘要，重点突出复试要点

---

### 案例 3：职场技能提升
**信息源：**
- 知乎：职场方法论
- 得到/混沌：专业课程笔记
- 36 氪/虎嗅：行业趋势分析

**标签：** Career Skill Improvement, Time Management

**输出：** 详细版摘要，包含 actionable suggestions

---

## 🔮 未来规划

- [ ] 接入真实 LLM API（如 ChatGPT、文心一言）
- [ ] 增加更多信息源（B 站、小红书等）
- [ ] 支持视频内容提取
- [ ] 多语言摘要生成
- [ ] 摘要质量评估反馈
- [ ] 用户账户系统
- [ ] 定时自动抓取
- [ ] 知识图谱可视化

---

## 👥 开发团队

**CDS547 Intro to Large Language Models - Group Project**

---

## 📄 许可证

MIT License - 仅供学习研究使用

---

## 🙏 致谢

感谢以下开源项目：
- Streamlit
- Flask
- BeautifulSoup
- Requests

---

## 📮 联系方式

如有问题，请通过以下方式联系：
- GitHub Issues
- 课程讨论区

---

**祝使用愉快！** 🎉
