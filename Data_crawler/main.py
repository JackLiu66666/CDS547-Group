import argparse
from typing import List

from crawlers import ZhihuCrawler, SinaNewsCrawler, WechatCrawler, ToutiaoCrawler, TencentNewsCrawler, NeteaseNewsCrawler
from llm_adapter import process_data_for_llm
from storage import ArticleStorage


def _load_urls_from_file(path: str) -> List[str]:
    urls: List[str] = []
    if not path:
        return urls
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                urls.append(line)
    except OSError:
        pass
    return urls


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="多源文章爬取与LLM预处理管道",
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=["zhihu", "sina", "wechat", "toutiao", "tencent_news", "netease_news"],
        default=["zhihu", "sina", "wechat", "toutiao", "tencent_news", "netease_news"],
        help="选择需要抓取的信息源，可多选",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=50,
        help="每个信息源最大抓取文章数量",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help='发布时间起始日期，格式 YYYY-MM-DD（目前主要对新浪新闻生效）',
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help='发布时间结束日期，格式 YYYY-MM-DD（目前主要对新浪新闻生效）',
    )
    parser.add_argument(
        "--zhihu-url-file",
        type=str,
        default=None,
        help="包含知乎专栏文章 URL 的文本文件（每行一个），用于精确控制抓取列表",
    )
    parser.add_argument(
        "--wechat-url-file",
        type=str,
        default=None,
        help="包含微信公众号公开文章 URL 的文本文件（每行一个）",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw_articles.jsonl",
        help="原始抓取结果保存路径（JSON Lines 格式）",
    )
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="仅抓取数据，不执行 LLM 预处理",
    )
    return parser.parse_args()


def run_pipeline(args: argparse.Namespace) -> None:
    print("=" * 60)
    print("数据爬取与 LLM 预处理管道启动")
    print("=" * 60)

    storage = ArticleStorage(path=args.output)

    # 1. 知乎（专栏文章）
    if "zhihu" in args.sources:
        zhihu_urls = _load_urls_from_file(args.zhihu_url_file)
        if zhihu_urls:
            print(f"[Zhihu] 计划抓取 {min(len(zhihu_urls), args.max_items)} 篇专栏文章")
            ZhihuCrawler().crawl_batch(
                urls=zhihu_urls,
                storage=storage,
                max_items=args.max_items,
            )
        else:
            print("[Zhihu] 未提供 URL 列表文件，跳过知乎抓取")

    # 2. 新浪新闻
    if "sina" in args.sources:
        print(f"[SinaNews] 计划抓取最多 {args.max_items} 篇新闻")
        SinaNewsCrawler().crawl_batch(
            storage=storage,
            max_items=args.max_items,
            start_date=args.start_date,
            end_date=args.end_date,
        )

    # 3. 微信公众号公开文章
    if "wechat" in args.sources:
        wechat_urls = _load_urls_from_file(args.wechat_url_file)
        if wechat_urls:
            print(
                f"[Wechat] 计划抓取 {min(len(wechat_urls), args.max_items)} 篇公众号文章"
            )
            WechatCrawler().crawl_batch(
                urls=wechat_urls,
                storage=storage,
                max_items=args.max_items,
            )
        else:
            print("[Wechat] 未提供 URL 列表文件，跳过公众号抓取")

    # 4. 今日头条
    if "toutiao" in args.sources:
        print(f"[Toutiao] 计划抓取最多 {args.max_items} 篇新闻")
        ToutiaoCrawler().crawl_batch(
            storage=storage,
            max_items=args.max_items,
        )

    # 5. 腾讯新闻
    if "tencent_news" in args.sources:
        print(f"[TencentNews] 计划抓取最多 {args.max_items} 篇新闻")
        TencentNewsCrawler().crawl_batch(
            storage=storage,
            max_items=args.max_items,
        )

    # 6. 网易新闻
    if "netease_news" in args.sources:
        print(f"[NeteaseNews] 计划抓取最多 {args.max_items} 篇新闻")
        NeteaseNewsCrawler().crawl_batch(
            storage=storage,
            max_items=args.max_items,
        )

    # 4. 将抓取的数据打包成 LLM 需要的 JSON 格式
    if not args.skip_llm:
        process_data_for_llm(input_path=args.output)


if __name__ == "__main__":
    cli_args = parse_args()
    run_pipeline(cli_args)