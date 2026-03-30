# 快速参考卡片 📋

## ⚡ 30 秒快速启动

```bash
# Windows 用户
.\start.bat

# 浏览器访问
http://localhost:8501
```

---

## 🎯 核心使用流程

### 三步生成摘要

```
1️⃣ 添加信息源 → 左侧边栏 → Add Sources
2️⃣ 设置兴趣标签 → Preset Tags + Custom Tags
3️⃣ 生成摘要 → Generate Aggregated Summary
```

**等待时间：** 30-60 秒  
**输出格式：** Word / PDF / Excel

---

## 🔧 常用命令

### 启动服务
```bash
# 一键启动（推荐）
.\start.bat

# 手动启动后端
cd Data_crawler && python api_server.py

# 手动启动前端
cd frontend && streamlit run app.py --server.port 8501
```

### 测试验证
```bash
# API 测试
python test_api.py

# 健康检查
curl http://localhost:5000/api/health
```

### 依赖管理
```bash
# 安装依赖
pip install -r requirements.txt

# 升级依赖
pip install -r requirements.txt --upgrade

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 🌐 端口说明

| 服务 | 端口 | 用途 |
|------|------|------|
| Flask API | 5000 | 后端 API 服务 |
| Streamlit | 8501 | 前端 UI 界面 |

**修改端口：**
```bash
# 后端
python api_server.py --port 5001

# 前端
streamlit run app.py --server.port 8502
```

---

## 📊 信息源类型

| 类型 | 代码 | 需要 URL | 说明 |
|------|------|---------|------|
| 知乎 | zhihu | ✅ | 专栏文章链接 |
| 新浪新闻 | sina | ❌ | 自动获取热门新闻 |
| 微信公众号 | wechat | ✅ | 公开文章链接 |
| 今日头条 | toutiao | ❌ | 自动获取热门新闻 |
| 腾讯新闻 | tencent_news | ❌ | 自动获取首页新闻 |
| 网易新闻 | netease_news | ❌ | 自动获取首页新闻 |

---

## 🏷️ 预设标签

```
✅ Latest AI Research        - AI 最新研究
✅ Grad Exam Prep Tips       - 考研经验技巧
✅ Career Skill Improvement  - 职业技能提升
✅ Hot News                  - 热点新闻
✅ Financial Trends          - 金融趋势
```

---

## 📝 输入示例

### 知乎（需要 URL）
```
https://zhuanlan.zhihu.com/p/123456
https://www.zhihu.com/question/789012
AI 大模型技术研究
```

### 微信公众号（需要 URL）
```
https://mp.weixin.qq.com/s/abcdefg
https://mp.weixin.qq.com/s/hijklmn
```

### 综合新闻（关键词即可）
```
人工智能最新进展
职场沟通技巧
时间管理方法论
```

---

## 🎛️ 摘要粒度

| 选项 | 字数 | 适用场景 |
|------|------|---------|
| Concise | <300 | 快速浏览、早报 |
| Standard | 500-800 | 日常学习（默认） |
| Detailed | >1000 | 深度研究、报告 |

---

## 🔍 API 接口速查

### 健康检查
```bash
GET /api/health
```

### 开始爬取
```bash
POST /api/crawl
{
  "sources": [{"type": "zhihu", "urls": [...]}],
  "max_items": 50
}
```

### 查询状态
```bash
GET /api/task/<task_id>
```

### 生成摘要
```bash
POST /api/generate_summary
{
  "articles": [...],
  "interest_tags": ["AI Research"],
  "granularity": "Standard"
}
```

### 下载文件
```bash
GET /api/download/<task_id>/raw   # 原始数据
GET /api/download/<task_id>/llm   # LLM 处理数据
```

---

## ⚠️ 常见错误速查

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| API 调用失败 | 后端未启动 | `cd Data_crawler && python api_server.py` |
| 端口被占用 | 端口已使用 | `netstat -ano \| findstr 5000` 杀死进程 |
| 爬取超时 | 网络问题 | 减少数量、稍后重试 |
| 依赖安装失败 | pip 版本低 | `python -m pip install --upgrade pip` |

---

## 💾 文件位置

```
data/raw_articles.jsonl    - 原始抓取数据
data/llm_ready.jsonl      - LLM 处理后的数据
temp/<task_id>/           - 临时任务文件
app.log                   - 应用日志
```

---

## 🎯 性能参考

| 规模 | 文章数 | 耗时 | 成功率 |
|------|--------|------|-------|
| 小型 | 10     | 20s  | 95%   |
| 中型 | 25     | 45s  | 92%   |
| 大型 | 50     | 90s  | 88%   |

---

## 📞 获取帮助

### 快速诊断
```bash
# 1. 检查 Python
python --version

# 2. 检查依赖
pip list

# 3. 检查端口
netstat -ano | findstr 5000
netstat -ano | findstr 8501

# 4. 测试 API
curl http://localhost:5000/api/health
```

### 查看日志
```bash
# 后端日志
tail -f Data_crawler/app.log

# 前端日志
# 浏览器 → F12 → Console
```

---

## 🚀 最佳实践 Tips

### ✅ Do's
- 优先使用 URL（比关键词精确）
- 标签设置 2-5 个为宜
- 单次不超过 20 个信息源
- 定期清理临时文件
- 使用标准版摘要（性价比最高）

### ❌ Don'ts
- 不要同时运行多个实例
- 不要设置过大的 max-items
- 避免高峰时段大量抓取
- 不要忽略错误提示

---

## 🎓 场景模板速查

### 场景 1：AI 研究追踪
```
信息源：知乎 AI 专栏 + 机器之心公众号
标签：Latest AI Research, LLM
粒度：Standard
频率：每周一次
```

### 场景 2：考研准备
```
信息源：知乎经验贴 + 考研公众号
标签：Grad Exam Prep Tips
粒度：Concise
频率：每天一次
```

### 场景 3：职场提升
```
信息源：得到 + 36 氪 + 知乎
标签：Career Skill Improvement
粒度：Detailed
频率：每周两次
```

---

## 📊 导出格式对比

| 格式 | 优点 | 适用场景 |
|------|------|---------|
| Word (.docx) | 可编辑 | 存档、修改 |
| PDF | 格式固定 | 打印、提交 |
| Excel (.xlsx) | 数据分析 | 批量处理、统计 |

---

## 🔧 配置文件速查

### config.py 关键参数
```python
CRAWL_PARAMS = {
    "retry_times": 2,        # 重试次数
    "delay_min": 1,          # 最小延时 (秒)
    "delay_max": 3,          # 最大延时 (秒)
    "batch_num": 10          # 批量数量
}
```

---

## 🎉 成功标志

```
✅ 后端启动 → "Running on http://0.0.0.0:5000"
✅ 前端启动 → "Local URL: http://localhost:8501"
✅ 测试通过 → "🎉 所有测试通过！系统运行正常"
✅ 爬取成功 → "进度：100% - 状态：completed"
```

---

## 📱 快捷方式

### Windows 快捷键
```
Ctrl + R     - 刷新页面
Ctrl + Shift + R - 强制刷新
F12          - 打开开发者工具
```

### Streamlit 快捷键
```
R            - 重新运行
D            - 切换暗色模式
```

---

## 🆘 紧急联系

**遇到问题？**
1. 查看 [README.md](README.md) - 完整文档
2. 查看 [QUICKSTART.md](QUICKSTART.md) - 快速入门
3. 查看 [DEPLOYMENT.md](DEPLOYMENT.md) - 部署指南
4. 运行 `python test_api.py` - 诊断问题

---

**祝使用愉快！** 🎈

*最后更新：2025-03-30*
