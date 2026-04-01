# LLM 辅助跨平台信息聚合与个性化摘要工具

单人完整开发成品，满足“跨平台聚合 + 用户自由搜索 + 个性化摘要 + 导出 + 性能统计”答辩要求。

## 1) 项目结构（核心四模块）

```text
llm_info_aggregator/
├─ app.py            # Streamlit 主界面（可交互 Demo）
├─ crawler.py        # 跨平台抓取（知乎/公众号/新闻/学术摘要）
├─ llm_core.py       # 国内 LLM API 适配与摘要生成
├─ utils.py          # 清洗去重/标签管理/导出/性能统计/数据集
├─ main.py           # 一键启动入口（streamlit run app.py）
├─ requirements.txt
├─ data/
│  ├─ custom_tags.json
│  └─ sample_dataset.jsonl   # 500+ 标注样本（默认600）
└─ outputs/
```

## 2) 一键运行（Cursor）

```bash
cd llm_info_aggregator
pip install -r requirements.txt
python main.py
```

或直接：

```bash
streamlit run app.py
```

## 3) 国内 LLM API 配置（OpenAI 兼容）

在页面侧边栏填写：
- `API Key`
- `Base URL`（示例：`https://api.deepseek.com/v1`、`https://api.siliconflow.cn/v1`）
- `Model`（示例：`deepseek-chat`）

未填 Key 时，系统自动启用本地回退摘要，确保演示稳定。

## 4) 必实现功能对应说明

- **跨平台抓取**：知乎、公众号、新闻、学术摘要四类，支持任意关键词自由搜索
- **数据处理**：清洗广告、去重、标准化字段、按兴趣标签分类
- **兴趣管理**：标签新增/编辑/删除
- **个性化摘要**：按“关键词 + 标签”定向摘要，避免无关内容
- **性能统计**：爬取成功率、摘要准确率估算（关键词覆盖法）
- **成果导出**：Word/PDF 一键下载
- **样本数据**：内置 600 条标注数据，可离线演示

## 5) 三大标准演示场景

- AI 研究动态：`大模型 Agent RAG`
- 考研备考：`考研 数学 英语 政治`
- 职场技能提升：`项目管理 数据分析 沟通`

并支持用户任意自由搜索，不做预设限制。
