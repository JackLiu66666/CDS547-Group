"""
API 测试脚本
用于验证后端 API 服务是否正常工作
"""
import requests
import time
import json

BASE_URL = "http://localhost:5000/api"


def test_health():
    """测试健康检查接口"""
    print("=" * 60)
    print("测试 1: 健康检查")
    print("=" * 60)
    
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"状态码：{resp.status_code}")
        print(f"响应内容：{json.dumps(resp.json(), indent=2, ensure_ascii=False)}")
        
        if resp.status_code == 200:
            print("✅ 健康检查通过")
            return True
        else:
            print("❌ 健康检查失败")
            return False
    except Exception as e:
        print(f"❌ 连接失败：{e}")
        print("请确保后端 API 服务正在运行：python Data_crawler/api_server.py")
        return False


def test_get_sources():
    """测试获取可用信息源"""
    print("\n" + "=" * 60)
    print("测试 2: 获取可用信息源")
    print("=" * 60)
    
    try:
        resp = requests.get(f"{BASE_URL}/sources", timeout=5)
        print(f"状态码：{resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            sources = data.get("sources", [])
            print(f"可用信息源数量：{len(sources)}")
            for source in sources:
                print(f"  - {source['name']} ({source['type']}): {source['description']}")
            print("✅ 信息源列表获取成功")
            return True
        else:
            print("❌ 获取信息源失败")
            return False
    except Exception as e:
        print(f"❌ 错误：{e}")
        return False


def test_crawl_task():
    """测试爬取任务（小规模）"""
    print("\n" + "=" * 60)
    print("测试 3: 爬取任务（小规模测试）")
    print("=" * 60)
    
    try:
        # 使用少量 URL 进行测试
        payload = {
            "sources": [
                {
                    "type": "sina",
                    "max_items": 3  # 只抓取 3 篇
                }
            ],
            "max_items_per_source": 3,
            "skip_llm": False
        }
        
        print("发送爬取请求...")
        resp = requests.post(f"{BASE_URL}/crawl", json=payload, timeout=10)
        print(f"状态码：{resp.status_code}")
        
        if resp.status_code == 200:
            result = resp.json()
            task_id = result.get("task_id")
            print(f"任务 ID: {task_id}")
            print(f"初始状态：{result.get('status')}")
            
            if not task_id:
                print("❌ 未获取到任务 ID")
                return False
            
            # 轮询任务状态
            print("\n等待任务完成...")
            max_attempts = 30
            for i in range(max_attempts):
                time.sleep(2)
                
                status_resp = requests.get(f"{BASE_URL}/task/{task_id}", timeout=5)
                if status_resp.status_code != 200:
                    continue
                
                status_data = status_resp.json()
                status = status_data.get("status")
                progress = status_data.get("progress", 0)
                
                print(f"  进度：{progress}% - 状态：{status}")
                
                if status == "completed":
                    result = status_data.get("result", {})
                    articles = result.get("articles", [])
                    print(f"\n✅ 任务完成！共抓取 {len(articles)} 篇文章")
                    
                    if articles:
                        print("\n第一篇文章示例:")
                        first = articles[0]
                        print(f"  标题：{first.get('title', 'N/A')}")
                        print(f"  来源：{first.get('source', 'N/A')}")
                        print(f"  作者：{first.get('author', 'N/A')}")
                        print(f"  URL: {first.get('url', 'N/A')}")
                    
                    return True
                elif status == "failed":
                    error = status_data.get("error", "未知错误")
                    print(f"\n❌ 任务失败：{error}")
                    return False
            
            print("\n⚠️  等待超时")
            return False
        else:
            print(f"❌ 爬取请求失败：{resp.text}")
            return False
            
    except Exception as e:
        print(f"❌ 错误：{e}")
        return False


def test_generate_summary():
    """测试摘要生成"""
    print("\n" + "=" * 60)
    print("测试 4: 摘要生成")
    print("=" * 60)
    
    try:
        # 模拟文章数据
        articles = [
            {
                "id": "test_1",
                "source": "zhihu",
                "title": "AI 研究最新进展",
                "content": "本文介绍了人工智能领域的最新研究成果，包括大语言模型、计算机视觉和强化学习等方面的突破。重点讨论了 GPT 系列模型的发展趋势和应用场景。",
                "url": "https://example.com/article1",
                "author": "张三",
                "published_at": "2025-03-28"
            },
            {
                "id": "test_2",
                "source": "wechat",
                "title": "职场技能提升指南",
                "content": "文章总结了职场人士必备的核心技能，包括时间管理、沟通技巧、学习能力等。提供了实用的方法论和案例分析。",
                "url": "https://example.com/article2",
                "author": "李四",
                "published_at": "2025-03-29"
            }
        ]
        
        payload = {
            "articles": articles,
            "interest_tags": ["AI Research", "Career Development"],
            "granularity": "Standard (500-800 words)"
        }
        
        print("发送摘要生成请求...")
        resp = requests.post(f"{BASE_URL}/generate_summary", json=payload, timeout=10)
        print(f"状态码：{resp.status_code}")
        
        if resp.status_code == 200:
            result = resp.json()
            print(f"\n✅ 摘要生成成功!")
            print(f"综合摘要：{result.get('overall_summary', '')[:100]}...")
            print(f"关键词：{', '.join(result.get('keywords', []))}")
            print(f"条目数：{len(result.get('item_summaries', []))}")
            return True
        else:
            print(f"❌ 摘要生成失败：{resp.text}")
            return False
            
    except Exception as e:
        print(f"❌ 错误：{e}")
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("LLM Information Aggregation API - 测试套件")
    print("=" * 60)
    
    # 检查 API 是否可访问
    if not test_health():
        print("\n" + "=" * 60)
        print("测试终止：API 服务不可用")
        print("=" * 60)
        return
    
    # 运行其他测试
    tests = [
        ("获取信息源", test_get_sources),
        ("爬取任务", test_crawl_task),
        ("摘要生成", test_generate_summary),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 测试 [{name}] 异常：{e}")
            results.append((name, False))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status} - {name}")
    
    print(f"\n总计：{passed}/{total} 个测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！系统运行正常")
    else:
        print("\n⚠️  部分测试失败，请检查配置和日志")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
