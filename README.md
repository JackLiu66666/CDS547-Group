# LLM 辅助跨平台信息聚合与个性化摘要工具

**CDS547 大语言模型导论课程项目**

一个智能的多源信息聚合系统，支持跨平台内容抓取、个性化摘要生成和多格式导出。

---

## 🌟 核心功能

- **跨平台聚合**：支持 Google News、Bing News、arXiv、Hacker News、GitHub、Wikipedia、StackOverflow 等多源信息
- **智能处理**：自动清洗、去重、标签分类
- **个性化摘要**：基于用户兴趣标签和粒度偏好生成定制摘要
- **多格式导出**：支持 Word、PDF 格式一键下载
- **性能统计**：爬取成功率、摘要准确率可视化展示

---

## 🚀 快速开始

### 一键启动（推荐）

**Windows 用户：**
```bash
# 双击运行
start.bat
```

或命令行：
```bash
.\start.bat
```

访问：**http://localhost:8501**

---

### 手动安装运行

#### 1. 安装依赖
```bash
pip install -r requirements.txt
```

#### 2. 启动应用
```bash
cd llm_info_aggregator
streamlit run app.py --server.port 8501
```

---

## 💻 使用指南

### 三步生成摘要

#### 1️⃣ 配置参数
在左侧边栏设置：
- **搜索关键词**：如 "人工智能"、"考研经验"
- **信息源选择**：Google News RSS、Bing News RSS、arXiv、Hacker News、GitHub Repos、Wikipedia、StackOverflow（建议至少 3 类）
- **每源抓取数量**：10-60 条
- **摘要长度**：200-1200 字

#### 2️⃣ 兴趣标签管理
- **预设标签**：AI 研究、考研备考、职场技能等
- **自定义标签**：支持新增、编辑、删除
- **示例标签**：`人工智能`, `时间管理`, `数据分析`

#### 3️⃣ 开始生成
点击「开始聚合与摘要」按钮

系统将自动执行：
1. **抓取** → 从各平台获取内容（约 30-60 秒）
2. **清洗** → 去重、标准化、标签分类
3. **摘要** → 按标签生成个性化摘要

---

### 查看和导出结果

#### 结果预览
- **左侧**：聚合内容列表（标题、来源、标签、链接）
- **右侧**：按标签分类的个性化摘要

#### 导出报告
点击底部「下载 Word/PDF 报告」按钮即可保存完整结果。

---

## 🎯 典型应用场景

### AI 研究动态追踪
- **关键词**：`LLM RAG Agent`
- **信息源**：arXiv + Hacker News + GitHub
- **标签**：人工智能

### 考研备考资料整理
- **关键词**：`graduate exam math english`
- **信息源**：Google News + Wikipedia + arXiv
- **标签**：考研

### 职场技能提升
- **关键词**：`project management communication analytics`
- **信息源**：Google News + Bing News + StackOverflow
- **标签**：职场技能

---

## 🔧 高级功能

### 国内 LLM API 配置（可选）

如需更高质量的摘要，可在侧边栏配置：
- **API Key**：你的密钥
- **Base URL**：如 `https://api.deepseek.com/v1`
- **Model**：如 `deepseek-chat`

**未配置时**：系统自动使用本地摘要算法，确保演示稳定。

---

### 标签管理

**新增标签：**
1. 在侧边栏输入新标签名
2. 点击「新增标签」

**编辑标签：**
1. 选择要编辑的标签
2. 输入新名称
3. 点击「编辑标签」

**删除标签：**
点击对应标签旁的「删除」按钮。

---

## 📊 系统架构

```
llm_info_aggregator/
├── app.py              # Streamlit 主界面
├── crawler.py          # 跨平台爬虫
├── llm_core.py         # LLM 摘要生成
├── utils.py            # 数据处理工具
└── src/
    ├── crawlers/       # 具体爬虫实现
    ├── processing/     # 清洗、标签分类
    ├── exporters/      # 导出功能
    └── utils/          # 工具函数
```

---

## 👥 开发团队

**CDS547 Intro to Large Language Models - Group Project**
