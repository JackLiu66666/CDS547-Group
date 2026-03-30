# 部署指南 🚀

## 📋 环境要求

### 最低配置
- **操作系统**: Windows 10 / macOS 10.15+ / Linux
- **Python**: 3.8 或更高版本
- **内存**: 4GB RAM
- **存储**: 500MB 可用空间
- **网络**: 稳定的互联网连接

### 推荐配置
- **操作系统**: Windows 11 / macOS 12+ / Ubuntu 20.04+
- **Python**: 3.10 或更高版本
- **内存**: 8GB RAM
- **存储**: 2GB 可用空间
- **网络**: 宽带连接（10Mbps+）

---

## 🔧 安装步骤

### Step 1: 检查 Python 环境

```bash
# 检查 Python 版本
python --version
# 应显示：Python 3.8.x 或更高

# 检查 pip 版本
pip --version
```

**如果未安装 Python：**
- Windows: 访问 https://www.python.org/downloads/
- macOS: `brew install python@3.10`
- Linux: `sudo apt-get install python3.10`

---

### Step 2: 克隆或下载项目

```bash
# 方式 1: Git 克隆
git clone <repository-url>
cd Group

# 方式 2: 直接下载 ZIP 解压
```

---

### Step 3: 安装依赖

```bash
# 方式 A: 使用 requirements.txt（推荐）
pip install -r requirements.txt

# 方式 B: 使用国内镜像加速
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 方式 C: 逐个安装（排查问题）
pip install requests beautifulsoup4 lxml flask flask-cors
pip install streamlit pandas plotly python-docx xhtml2pdf reportlab Pillow
```

**验证安装：**
```bash
pip list | grep -E "requests|flask|streamlit|beautifulsoup"
```

---

### Step 4: 启动服务

#### 方式 A: 一键启动（Windows）
```bash
.\start.bat
```

#### 方式 B: 手动启动

**终端 1 - 后端 API:**
```bash
cd Data_crawler
python api_server.py
```

预期输出：
```
============================================================
LLM Information Aggregation API Server
============================================================
Starting server at http://localhost:5000
API Documentation:
  GET  /api/health          - Health check
  POST /api/crawl           - Start crawl task
  ...
============================================================
 * Serving Flask app 'api_server'
 * Debug mode: on
 * Running on http://0.0.0.0:5000
```

**终端 2 - 前端 UI:**
```bash
cd frontend
streamlit run app.py --server.port 8501
```

预期输出：
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
  External URL: http://203.0.113.x:8501
```

---

### Step 5: 访问应用

打开浏览器访问：**http://localhost:8501**

首次加载可能需要 10-20 秒，请耐心等待。

---

## 🧪 验证安装

### 运行测试脚本

```bash
python test_api.py
```

**预期输出：**
```
============================================================
LLM Information Aggregation API - 测试套件
============================================================
测试 1: 健康检查
============================================================
状态码：200
响应内容：{
  "status": "healthy",
  "timestamp": "2025-03-30T15:47:40",
  "service": "LLM Information Aggregation API"
}
✅ 健康检查通过

测试 2: 获取可用信息源
============================================================
状态码：200
可用信息源数量：6
  - 知乎 (zhihu): 知乎专栏文章
  - 新浪新闻 (sina): 新浪新闻滚动新闻
  ...
✅ 信息源列表获取成功

...

总计：4/4 个测试通过
🎉 所有测试通过！系统运行正常
```

---

## 🐛 故障排查

### 问题 1: 依赖安装失败

**症状：**
```
ERROR: Could not find a version that satisfies the requirement xxx
```

**解决方案：**
```bash
# 1. 升级 pip
python -m pip install --upgrade pip
python -m pip install --upgrade setuptools

# 2. 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 逐个安装排查问题包
pip install requests
pip install beautifulsoup4
pip install flask
# ... 找出失败的包
```

---

### 问题 2: 端口被占用

**症状：**
```
OSError: [WinError 10048] Only one usage of each socket address
```

**解决方案：**

```bash
# Windows - 查找占用端口的进程
netstat -ano | findstr :5000
netstat -ano | findstr :8501

# 杀死进程（替换 PID）
taskkill /F /PID <找到的 PID>

# 或者修改端口
streamlit run app.py --server.port 8502
python api_server.py --port 5001
```

---

### 问题 3: 后端无法启动

**症状：**
```
ModuleNotFoundError: No module named 'flask'
```

**解决方案：**
```bash
# 确认已安装 flask
pip list | findstr flask

# 重新安装
pip uninstall flask
pip install flask flask-cors

# 检查 Python 路径
python -c "import sys; print(sys.executable)"
python -c "import flask; print(flask.__file__)"
```

---

### 问题 4: 前端无法连接后端

**症状：**
```
网络错误：HTTPConnectionPool(host='localhost', port=5000)
```

**解决方案：**

1. **检查后端是否运行**
```bash
curl http://localhost:5000/api/health
```

2. **检查防火墙设置**
```bash
# Windows - 允许端口
netsh advfirewall firewall add rule name="Flask API" dir=in action=allow protocol=TCP localport=5000
```

3. **检查 CORS 配置**
```python
# api_server.py 中确认有这行
CORS(app)  # 允许跨域请求
```

---

### 问题 5: 爬虫抓取失败

**症状：**
```
爬取失败：HTTPSConnectionPool(host='zhuanlan.zhihu.com', port=443)
```

**解决方案：**

1. **检查网络连接**
```bash
ping zhuanlan.zhihu.com
```

2. **降低并发数量**
```python
# config.py
CRAWL_PARAMS = {
    "retry_times": 2,
    "delay_min": 2,      # 增加最小延时
    "delay_max": 5,      # 增加最大延时
    "batch_num": 5       # 减少批量数量
}
```

3. **更新 User-Agent**
```python
# config.py
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ..."
}
```

---

## 📦 打包部署（可选）

### 创建独立运行的 EXE

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包后端
cd Data_crawler
pyinstaller --onefile --name api_server api_server.py

# 打包前端
cd frontend
pyinstaller --onefile --name run_app run_app.py
```

**注意：** 由于 Streamlit 的复杂性，建议前端仍使用脚本方式运行。

---

## ☁️ 云端部署

### Docker 部署（开发中）

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

EXPOSE 5000 8501

CMD ["./start.sh"]
```

**运行：**
```bash
docker build -t llm-aggregator .
docker run -p 5000:5000 -p 8501:8501 llm-aggregator
```

---

### Heroku 部署

1. **创建 Procfile**
```
web: cd Data_crawler && python api_server.py & cd frontend && streamlit run app.py --server.port $PORT
```

2. **创建 runtime.txt**
```
python-3.10.13
```

3. **部署**
```bash
heroku create your-app-name
git push heroku main
```

---

## 🔒 安全建议

### 1. 生产环境配置

```python
# api_server.py
if __name__ == '__main__':
    # 关闭 debug 模式
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,  # ⚠️ 重要：生产环境关闭 debug
        threaded=True
    )
```

---

### 2. 添加认证

```python
from flask import request, jsonify
import os

API_KEY = os.environ.get('API_KEY', 'your-secret-key')

@app.before_request
def check_auth():
    if request.path.startswith('/api/'):
        token = request.headers.get('X-API-Key')
        if token != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
```

---

### 3. 限流保护

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/crawl', methods=['POST'])
@limiter.limit("10 per minute")
def crawl():
    ...
```

---

## 📊 性能监控

### 添加日志记录

```python
import logging
from logging.handlers import RotatingFileHandler

# 配置日志
handler = RotatingFileHandler(
    'app.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=10
)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s'
))

app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

@app.route('/api/crawl', methods=['POST'])
def crawl():
    app.logger.info(f"Crawl request received: {request.json}")
    ...
```

---

## 🔄 自动更新

### 创建更新脚本

**update.bat (Windows):**
```batch
@echo off
echo 正在更新依赖...
pip install -r requirements.txt --upgrade
echo 更新完成！
pause
```

**update.sh (Linux/Mac):**
```bash
#!/bin/bash
echo "正在更新依赖..."
pip install -r requirements.txt --upgrade
echo "更新完成！"
```

---

## 📝 维护清单

### 每日检查
- [ ] 后端 API 可访问
- [ ] 前端页面可打开
- [ ] 爬取功能正常
- [ ] 日志文件大小正常

### 每周维护
- [ ] 清理临时文件
- [ ] 检查依赖更新
- [ ] 审查错误日志
- [ ] 备份重要数据

### 每月任务
- [ ] 更新 User-Agent
- [ ] 测试所有信息源
- [ ] 性能基准测试
- [ ] 安全检查

---

## 🆘 常见问题 FAQ

### Q1: 第一次启动很慢？
**A:** 首次启动需要加载所有依赖，属正常现象。后续启动会快很多。

### Q2: 为什么有些网站抓取失败？
**A:** 可能原因：
- 网站反爬机制
- 网络连接问题
- URL 已失效
- 需要登录才能访问

### Q3: 如何查看详细的错误信息？
**A:** 
```bash
# 后端以 debug 模式运行
python api_server.py
# 观察控制台输出

# 查看日志文件
tail -f Data_crawler/app.log
```

### Q4: 可以在服务器上运行吗？
**A:** 可以，但建议：
- 关闭 debug 模式
- 添加认证机制
- 配置防火墙规则
- 使用进程管理工具（如 supervisor）

### Q5: 支持多用户同时使用吗？
**A:** 当前版本支持有限并发，建议：
- 单用户使用
- 如需多用户，请升级到 V2.0（规划中）

---

## 📞 获取帮助

### 日志位置
- **后端日志**: `Data_crawler/app.log`
- **前端日志**: 浏览器开发者工具 Console

### 诊断命令
```bash
# 检查 Python 环境
python --version
pip --version

# 检查依赖
pip list

# 检查端口
netstat -ano | findstr 5000
netstat -ano | findstr 8501

# 测试 API
curl http://localhost:5000/api/health
```

---

## ✅ 部署检查清单

部署完成后，请确认：

- [ ] Python 3.8+ 已安装
- [ ] 所有依赖已安装成功
- [ ] 后端 API 在 5000 端口运行
- [ ] 前端 UI 在 8501 端口运行
- [ ] 可以通过浏览器访问 http://localhost:8501
- [ ] 测试爬取功能正常
- [ ] 测试摘要生成功能正常
- [ ] 测试导出功能正常
- [ ] 日志文件正常写入

**全部确认通过后，系统即可投入使用！** 🎉

---

**祝部署顺利！** 如有问题，请参考 README.md 或查阅 QUICKSTART.md。
