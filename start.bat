@echo off
chcp 65001 >nul
echo ============================================================
echo LLM 跨平台信息聚合与个性化摘要工具 - 启动程序
echo ============================================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [1/3] 检查 Python 环境...
python -c "import sys; print(f'Python {sys.version}')"

echo.
echo [2/3] 安装依赖包...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [警告] 依赖安装可能有问题，继续尝试启动...
)

echo.
echo [3/3] 启动前端界面...
echo      - 前端地址：http://localhost:8501
start "LLM Frontend" cmd /k "cd llm_info_aggregator && streamlit run app.py --server.port 8501"

echo.
echo ============================================================
echo 启动完成！
echo ============================================================
echo.
echo 服务访问地址:
echo   前端界面：http://localhost:8501
echo.
echo 按任意键打开浏览器...
pause >nul

start http://localhost:8501

exit /b 0
