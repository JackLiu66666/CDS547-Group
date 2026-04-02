import streamlit as st

from crawler import CrossPlatformCrawler
from llm_core import DomesticLLM
from utils import (
    annotate_interest_tags,
    crawl_success_rate,
    deduplicate_items,
    enrich_items_for_display,
    ensure_dataset,
    export_pdf,
    export_word,
    filter_by_search_keyword,
    filter_items_by_selected_keywords,
    load_dataset,
    save_json,
    summary_accuracy_estimate,
    to_dataframe,
)


def run():
    st.set_page_config(page_title="LLM信息聚合摘要工具", layout="wide")
    st.title("LLM 辅助跨平台信息聚合与个性化摘要工具")
    st.caption("两阶段流程：先检索+LLM预分析标签，再按标签二次精准筛选")
    ensure_dataset(600)

    with st.sidebar:
        st.header("搜索与参数")
        keyword = st.text_input("自由搜索关键词", value="人工智能")
        sources = st.multiselect(
            "选择信息源（建议至少3类）",
            options=["Google News RSS", "Bing News RSS", "arXiv", "Hacker News", "GitHub Repos", "Wikipedia", "StackOverflow"],
            default=["Google News RSS", "Bing News RSS", "arXiv"],
        )
        max_items = st.slider("每源抓取上限", 10, 60, 25, 5)
        summary_len = st.slider("摘要长度", 200, 1200, 500, 50)
        use_sample = st.toggle("拼接内置样本（仅演示）", False)
        use_llm_semantic_filter = st.toggle("启用LLM语义筛选（消耗Token）", True)

        st.divider()
        st.subheader("国内 LLM API 配置")
        api_key = st.text_input("API Key", type="password", help="推荐使用环境变量或临时输入，避免写入代码")
        base_url = st.text_input("Base URL", value="https://api.deepseek.com")
        model = st.text_input("Model", value="deepseek-chat")

    if "items" not in st.session_state:
        st.session_state["items"] = []
    if "display_items" not in st.session_state:
        st.session_state["display_items"] = []
    if "recommended_tags" not in st.session_state:
        st.session_state["recommended_tags"] = []
    if "pre_overview" not in st.session_state:
        st.session_state["pre_overview"] = ""
    if "summaries" not in st.session_state:
        st.session_state["summaries"] = {}
    if "stats" not in st.session_state:
        st.session_state["stats"] = {}

    if st.button("1) 检索并执行LLM预分析", type="primary"):
        if len(sources) < 3:
            st.info("建议至少选择3类信息源，可获得更稳定、全面的结果。")

        with st.spinner("检索并进行LLM预分析中..."):
            crawler = CrossPlatformCrawler(timeout=10)
            crawled, stats = crawler.crawl(keyword=keyword, selected_sources=sources, max_items=max_items)
            samples = load_dataset(limit=180) if use_sample else []
            samples = filter_by_search_keyword(samples, keyword) if samples else []
            combined = deduplicate_items(crawled + samples)
            filtered = filter_by_search_keyword(combined, keyword)

            llm = DomesticLLM(api_key=api_key, base_url=base_url, model=model)
            pre = llm.pre_analyze_results(filtered, keyword=keyword, summary_len=summary_len, top_k_tags=12)

            st.session_state["items"] = filtered
            st.session_state["display_items"] = filtered
            st.session_state["stats"] = stats
            st.session_state["recommended_tags"] = pre.get("recommended_tags", [])
            st.session_state["pre_overview"] = pre.get("overview", "")
            st.session_state["summaries"] = {}
            save_json(filtered, "latest_results.json")
        st.success(
            f"预分析完成：共 {len(st.session_state['items'])} 条信息，推荐标签 {len(st.session_state['recommended_tags'])} 个。"
        )

    if st.session_state["items"]:
        st.subheader("LLM预分析结果")
        st.write(st.session_state["pre_overview"] or "暂无预分析摘要。")
        selected_keywords = st.multiselect(
            "请选择LLM推荐兴趣标签（用于二次精准筛选）",
            options=st.session_state["recommended_tags"],
            default=[],
        )
        if st.button("2) 按所选兴趣标签执行二次精准筛选"):
            local_filtered = filter_items_by_selected_keywords(
                st.session_state["items"], selected_keywords
            )
            local_filtered = annotate_interest_tags(local_filtered, selected_keywords, "")
            if use_llm_semantic_filter:
                llm_for_filter = DomesticLLM(api_key=api_key, base_url=base_url, model=model)
                st.session_state["display_items"] = llm_for_filter.semantic_filter_items(
                    local_filtered,
                    keyword=keyword,
                    selected_keywords=selected_keywords,
                    top_n=80,
                )
            else:
                st.session_state["display_items"] = local_filtered

            llm = DomesticLLM(api_key=api_key, base_url=base_url, model=model)
            st.session_state["summaries"] = llm.summarize_by_interest(
                st.session_state["display_items"],
                selected_keywords if selected_keywords else ["搜索词总结"],
                keyword,
                summary_len=summary_len,
                use_interest_tags=bool(selected_keywords),
            )
            st.success(f"二次筛选完成：剩余 {len(st.session_state['display_items'])} 条。")
    else:
        selected_keywords = []

    left, right = st.columns([2, 1])
    with left:
        st.subheader("聚合结果")
        df = to_dataframe(enrich_items_for_display(st.session_state["display_items"]))
        if not df.empty:
            show_cols = ["title", "source_type", "source_name", "publish_time", "interest_tags", "display_url"]
            st.dataframe(df[show_cols], use_container_width=True)
        else:
            st.info("当前筛选条件下暂无结果，可减少关键词筛选或重新搜索。")

    with right:
        st.subheader("二次筛选后摘要")
        if st.session_state["summaries"]:
            for tag, text in st.session_state["summaries"].items():
                st.markdown(f"**{tag}**")
                st.write(text)
        else:
            st.info("请先完成二次筛选后再查看摘要。")

    st.divider()
    st.subheader("性能统计")
    stats = st.session_state["stats"]
    success_rate = crawl_success_rate(stats)
    merged_summary = "\n".join(st.session_state["summaries"].values()) if st.session_state["summaries"] else ""
    acc = summary_accuracy_estimate(st.session_state["display_items"], merged_summary)
    c1, c2 = st.columns(2)
    c1.metric("爬取成功率", f"{success_rate * 100:.1f}%")
    c2.metric("摘要准确率(估算)", f"{acc * 100:.1f}%")
    if stats:
        st.json(stats)

    st.divider()
    st.subheader("导出报告")
    if st.session_state["display_items"]:
        word_path = export_word(st.session_state["display_items"], st.session_state["summaries"], "report.docx")
        pdf_path = export_pdf(st.session_state["display_items"], st.session_state["summaries"], "report.pdf")
        with open(word_path, "rb") as f:
            st.download_button("下载 Word", f, file_name="report.docx")
        with open(pdf_path, "rb") as f:
            st.download_button("下载 PDF", f, file_name="report.pdf")

    st.divider()
    st.subheader("三大标准场景 + 自由搜索")
    st.markdown(
        "- AI研究动态：关键词 `LLM RAG Agent`（来源建议：arXiv + Hacker News + GitHub）\n"
        "- 考研备考：关键词 `graduate exam math english`（来源建议：Google News + Wikipedia + arXiv）\n"
        "- 职场技能提升：关键词 `project management communication analytics`\n"
        "- 用户自由搜索：任意关键词，系统先生成推荐标签，再二次筛选。"
    )


if __name__ == "__main__":
    run()
