"""
LLM Information Aggregation API Server
提供 RESTful API 接口供前端调用
"""
import os
import sys
import uuid
import json
from datetime import datetime
from typing import List, Dict, Any
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import threading
import tempfile
import shutil

# 导入后端模块
from main import run_pipeline, parse_args
from storage import ArticleStorage
from llm_adapter import process_data_for_llm
from llm_adapter import extract_secondary_keywords
from models import Article
from crawlers import (
    ZhihuCrawler, SinaNewsCrawler, WechatCrawler, 
    ToutiaoCrawler, TencentNewsCrawler, NeteaseNewsCrawler
)

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 全局任务存储
tasks: Dict[str, Dict[str, Any]] = {}

# 临时目录配置
TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)


def cleanup_temp_dir(task_id: str):
    """清理临时文件"""
    temp_path = os.path.join(TEMP_DIR, task_id)
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)


def get_crawler(source_type: str):
    """根据信息源类型获取爬虫实例"""
    crawler_map = {
        "zhihu": ZhihuCrawler,
        "sina": SinaNewsCrawler,
        "wechat": WechatCrawler,
        "toutiao": ToutiaoCrawler,
        "tencent_news": TencentNewsCrawler,
        "netease_news": NeteaseNewsCrawler,
    }
    crawler_class = crawler_map.get(source_type.lower())
    if crawler_class:
        return crawler_class()
    raise ValueError(f"Unsupported source type: {source_type}")


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "LLM Information Aggregation API"
    })


@app.route('/api/crawl', methods=['POST'])
def crawl():
    """
    爬取数据接口
    Request Body:
    {
        "sources": [
            {"type": "zhihu", "urls": ["url1", "url2"]},
            {"type": "sina", "max_items": 50, "start_date": "2025-01-01", "end_date": "2025-03-30"},
            ...
        ],
        "max_items_per_source": 50,
        "skip_llm": false
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        sources = data.get('sources', [])
        if not sources:
            return jsonify({"error": "At least one source is required"}), 400
        
        # 生成任务 ID
        task_id = str(uuid.uuid4())
        
        # 创建临时目录
        task_temp_dir = os.path.join(TEMP_DIR, task_id)
        os.makedirs(task_temp_dir, exist_ok=True)
        
        output_file = os.path.join(task_temp_dir, "raw_articles.jsonl")
        llm_output_file = os.path.join(task_temp_dir, "llm_ready.jsonl")
        
        # 保存任务状态
        tasks[task_id] = {
            "status": "processing",
            "created_at": datetime.now().isoformat(),
            "sources": sources,
            "progress": 0,
            "result": None,
            "error": None,
            "temp_dir": task_temp_dir
        }
        
        # 异步执行爬取任务
        def run_crawl_task():
            try:
                all_articles = []
                total_sources = len(sources)
                
                for idx, source in enumerate(sources):
                    source_type = source.get('type', '')
                    max_items = source.get('max_items', data.get('max_items_per_source', 50))
                    
                    try:
                        crawler = get_crawler(source_type)
                        storage = ArticleStorage(path=output_file)
                        
                        # 根据不同类型调用不同参数
                        if source_type in ['zhihu', 'wechat']:
                            urls = source.get('urls', [])
                            if urls:
                                articles = crawler.crawl_batch(
                                    urls=urls,
                                    storage=storage,
                                    max_items=max_items
                                )
                                all_articles.extend([a.to_dict() for a in articles])
                        elif source_type == 'sina':
                            articles = crawler.crawl_batch(
                                storage=storage,
                                max_items=max_items,
                                start_date=source.get('start_date'),
                                end_date=source.get('end_date')
                            )
                            all_articles.extend([a.to_dict() for a in articles])
                        else:
                            articles = crawler.crawl_batch(
                                storage=storage,
                                max_items=max_items
                            )
                            all_articles.extend([a.to_dict() for a in articles])
                        
                        # 更新进度
                        tasks[task_id]['progress'] = int((idx + 1) / total_sources * 100)
                        
                    except Exception as e:
                        tasks[task_id]['error'] = f"Error crawling {source_type}: {str(e)}"
                        continue
                
                # 处理 LLM 数据
                if not data.get('skip_llm', False) and all_articles:
                    process_data_for_llm(
                        input_path=output_file,
                        output_path=llm_output_file
                    )
                    
                    # 读取 LLM 处理后的数据
                    llm_data = []
                    if os.path.exists(llm_output_file):
                        with open(llm_output_file, 'r', encoding='utf-8') as f:
                            for line in f:
                                line = line.strip()
                                if line:
                                    try:
                                        llm_data.append(json.loads(line))
                                    except json.JSONDecodeError:
                                        continue
                
                # 完成任务
                tasks[task_id]['status'] = 'completed'
                tasks[task_id]['result'] = {
                    "articles": all_articles,
                    "llm_processed": llm_data if not data.get('skip_llm', False) else [],
                    "total_count": len(all_articles),
                    "output_file": output_file,
                    "llm_output_file": llm_output_file
                }
                
            except Exception as e:
                tasks[task_id]['status'] = 'failed'
                tasks[task_id]['error'] = str(e)
        
        # 启动后台线程
        thread = threading.Thread(target=run_crawl_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "task_id": task_id,
            "status": "processing",
            "message": "Crawl task started successfully"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/task/<task_id>', methods=['GET'])
def get_task_status(task_id: str):
    """查询任务状态"""
    task = tasks.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    return jsonify({
        "task_id": task_id,
        "status": task['status'],
        "progress": task['progress'],
        "created_at": task['created_at'],
        "error": task['error'],
        "result": task['result'] if task['status'] == 'completed' else None
    })


@app.route('/api/download/<task_id>/<file_type>', methods=['GET'])
def download_file(task_id: str, file_type: str):
    """下载结果文件"""
    task = tasks.get(task_id)
    if not task or not task.get('result'):
        return jsonify({"error": "Task not found or not completed"}), 404
    
    if file_type == 'raw':
        file_path = task['result'].get('output_file')
    elif file_type == 'llm':
        file_path = task['result'].get('llm_output_file')
    else:
        return jsonify({"error": "Invalid file type"}), 400
    
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=f"{task_id}_{file_type}.jsonl",
        mimetype='application/jsonl'
    )


@app.route('/api/sources', methods=['GET'])
def get_available_sources():
    """获取可用的信息源列表"""
    return jsonify({
        "sources": [
            {
                "type": "zhihu",
                "name": "知乎",
                "description": "知乎专栏文章",
                "requires_urls": True
            },
            {
                "type": "sina",
                "name": "新浪新闻",
                "description": "新浪新闻滚动新闻",
                "supports_date_filter": True
            },
            {
                "type": "wechat",
                "name": "微信公众号",
                "description": "微信公众号公开文章",
                "requires_urls": True
            },
            {
                "type": "toutiao",
                "name": "今日头条",
                "description": "今日头条热门新闻",
                "auto_fetch_urls": True
            },
            {
                "type": "tencent_news",
                "name": "腾讯新闻",
                "description": "腾讯新闻首页新闻",
                "auto_fetch_urls": True
            },
            {
                "type": "netease_news",
                "name": "网易新闻",
                "description": "网易新闻首页新闻",
                "auto_fetch_urls": True
            }
        ]
    })


@app.route('/api/generate_summary', methods=['POST'])
def generate_summary():
    """
    生成个性化摘要（模拟实现，可接入真实 LLM）
    Request Body:
    {
        "articles": [...],
        "interest_tags": ["tag1", "tag2"],
        "granularity": "Standard (500-800 words)"
    }
    """
    try:
        data = request.json
        articles = data.get('articles', [])
        interest_tags = data.get('interest_tags', [])
        granularity = data.get('granularity', 'Standard (500-800 words)')
        
        if not articles:
            return jsonify({"error": "No articles provided"}), 400
        
        if not interest_tags:
            return jsonify({"error": "Interest tags are required"}), 400
        
        # 生成摘要（这里使用模板，实际应调用 LLM API）
        item_summaries = []
        for article in articles:
            item_summaries.append({
                "id": article.get('id', ''),
                "platform": article.get('source', ''),
                "title": article.get('title', ''),
                "url": article.get('url', ''),
                "published_at": article.get('published_at', ''),
                "author": article.get('author', ''),
                "summary": f"本文内容与标签 {', '.join(interest_tags)} 相关。核心观点聚焦于趋势判断、实践路径和可行建议，适合作为{granularity}的输入素材。",
                "raw_text": article.get('content', '')
            })
        
        overall_summary = (
            f"本次共聚合了 {len(articles)} 条有效信息，围绕 {', '.join(interest_tags)} 等标签生成个性化摘要。"
            f"总体而言，各平台信息在深度和时效性上互为补充：学术和专业内容提供方法论支撑，"
            f"社区和新闻内容提供场景案例和趋势信号。建议优先关注高频共识点，并结合个人目标进行实践。"
        )
        
        return jsonify({
            "overall_summary": overall_summary,
            "item_summaries": item_summaries,
            "keywords": interest_tags + ["趋势分析", "方法论", "实践建议"],
            "generated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===================== 新增：二次筛选关键词API =====================
@app.route("/api/secondary_keywords", methods=["POST"])
def get_secondary_keywords():
    data = request.json
    text = data.get("text", "")
    is_english = data.get("is_english", True)
    keywords = extract_secondary_keywords(text, is_english)
    return jsonify({"keywords": keywords})


if __name__ == '__main__':
    print("=" * 60)
    print("LLM Information Aggregation API Server")
    print("=" * 60)
    print("Starting server at http://localhost:5000")
    print("API Documentation:")
    print("  GET  /api/health          - Health check")
    print("  POST /api/crawl           - Start crawl task")
    print("  GET  /api/task/<id>       - Get task status")
    print("  GET  /api/download/<id>   - Download result files")
    print("  GET  /api/sources         - Get available sources")
    print("  POST /api/generate_summary - Generate personalized summary")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
