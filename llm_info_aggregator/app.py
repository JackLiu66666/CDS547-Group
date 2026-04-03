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
    st.set_page_config(page_title="LLM Information Aggregation and Summary Tool", layout="wide")
    st.title("LLM-Assisted Cross-Platform Information Aggregation and Personalized Summary Tool")
    st.caption("Two-stage process: first retrieve + LLM pre-analysis tags, then perform secondary precise filtering by tags")
    ensure_dataset(600)

    with st.sidebar:
        st.header("Search and Parameters")
        keyword = st.text_input("Free search keyword", value="Artificial Intelligence")
        sources = st.multiselect(
            "Select information sources (recommend at least 3 types)",
            options=["Google News RSS", "Bing News RSS", "arXiv", "Hacker News", "GitHub Repos", "Wikipedia", "StackOverflow"],
            default=["Google News RSS", "Bing News RSS", "arXiv"],
        )
        max_items = st.slider("Per-source crawl limit", 10, 60, 25, 5)
        summary_len = st.slider("Summary length", 200, 1200, 500, 50)
        use_sample = st.toggle("Include built-in samples (demo only)", False)
        use_llm_semantic_filter = st.toggle("Enable LLM semantic filtering (consumes tokens)", True)

        st.divider()
        st.subheader("Domestic LLM API Configuration")
        api_key = st.text_input("API Key", type="password", help="Recommended to use environment variables or temporary input, avoid writing to code")
        base_url = st.text_input(
            "Base URL", 
            value="https://api.deepseek.com", 
            help="DeepSeek: https://api.deepseek.com (without /v1) | SiliconFlow: https://api.siliconflow.cn/v1 | Doubao: https://ark.cn-beijing.volces.com/api/v3"
        )
        model = st.text_input(
            "Model", 
            value="deepseek-chat", 
            help="DeepSeek: deepseek-chat | SiliconFlow: Qwen/Qwen2.5-72B-Instruct | Doubao: doubao-seed-2-0-lite-260215"
        )

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
    if "last_llm_debug_info" not in st.session_state:
        st.session_state["last_llm_debug_info"] = []

    if st.button("1) Retrieve and perform LLM pre-analysis", type="primary"):
        if len(sources) < 3:
            st.info("It is recommended to select at least 3 types of information sources for more stable and comprehensive results.")

        with st.spinner("Retrieving and performing LLM pre-analysis..."):
            crawler = CrossPlatformCrawler(timeout=10)
            crawled, stats = crawler.crawl(keyword=keyword, selected_sources=sources, max_items=max_items)
            samples = load_dataset(limit=180) if use_sample else []
            samples = filter_by_search_keyword(samples, keyword) if samples else []
            combined = deduplicate_items(crawled + samples)
            filtered = filter_by_search_keyword(combined, keyword)

            llm = DomesticLLM(api_key=api_key, base_url=base_url, model=model)
            pre = llm.pre_analyze_results(filtered, keyword=keyword, summary_len=summary_len, top_k_tags=12)
            
            # Save LLM debug info to session_state
            st.session_state["last_llm_debug_info"] = llm.debug_info if hasattr(llm, 'debug_info') else []

            st.session_state["items"] = filtered
            st.session_state["display_items"] = filtered
            st.session_state["stats"] = stats
            st.session_state["recommended_tags"] = pre.get("recommended_tags", [])
            st.session_state["pre_overview"] = pre.get("overview", "")
            st.session_state["summaries"] = {}
            save_json(filtered, "latest_results.json")
        st.success(
            f"Pre-analysis completed: {len(st.session_state['items'])} items in total, {len(st.session_state['recommended_tags'])} recommended tags."
        )

    if st.session_state["items"]:
        st.subheader("LLM Pre-analysis Results")
        
        # Display pre-analysis summary
        if st.session_state["pre_overview"]:
            st.success("✅ Pre-analysis completed")
            st.write(st.session_state["pre_overview"])
        else:
            st.info("No pre-analysis summary available.")
        
        # Display debug information (with warning colors)
        with st.expander("🔍 View LLM call details", expanded=False):
            debug_info = st.session_state.get("last_llm_debug_info", [])
            if debug_info:
                for log in debug_info:
                    # Use different colors based on log type
                    if "❌" in log or "⚠️" in log:
                        st.error(log)
                    elif "✅" in log:
                        st.success(log)
                    else:
                        st.code(log)
                
                # If there's a Content Exists Risk error, display specific handling suggestions
                if any("Content Exists Risk" in log for log in debug_info):
                    st.warning("""
                    **⚠️ Content security risk detected**
                    
                    This is usually because the search keyword or crawled content triggered the AI service's security filtering mechanism.
                    
                    **Handling suggestions:**
                    1. Use a more neutral, academic search keyword
                    2. Check if crawled content contains advertisements or prohibited information
                    3. Try reducing the temperature parameter in API calls
                    4. If the issue persists, temporarily disable LLM functionality and use local fallback algorithms
                    """)
            else:
                st.info("No debug information available")
        
        selected_keywords = st.multiselect(
            "Select LLM-recommended interest tags (for secondary precise filtering)",
            options=st.session_state["recommended_tags"],
            default=[],
        )
        if st.button("2) Perform secondary precise filtering by selected interest tags"):
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
                selected_keywords if selected_keywords else ["Search Term Summary"],
                keyword,
                summary_len=summary_len,
                use_interest_tags=bool(selected_keywords),
            )
            st.success(f"Secondary filtering completed: {len(st.session_state['display_items'])} items remaining.")
    else:
        selected_keywords = []

    left, right = st.columns([2, 1])
    with left:
        st.subheader("Aggregation Results")
        df = to_dataframe(enrich_items_for_display(st.session_state["display_items"]))
        if not df.empty:
            show_cols = ["title", "source_type", "source_name", "publish_time", "interest_tags", "display_url"]
            st.dataframe(df[show_cols], use_container_width=True)
        else:
            st.info("No results under current filtering conditions. Try reducing keyword filtering or re-searching.")

    with right:
        st.subheader("Summaries after Secondary Filtering")
        if st.session_state["summaries"]:
            for tag, text in st.session_state["summaries"].items():
                st.markdown(f"**{tag}**")
                st.write(text)
        else:
            st.info("Please complete secondary filtering before viewing summaries.")

    st.divider()
    st.subheader("Performance Statistics")
    stats = st.session_state["stats"]
    success_rate = crawl_success_rate(stats)
    merged_summary = "\n".join(st.session_state["summaries"].values()) if st.session_state["summaries"] else ""
    acc = summary_accuracy_estimate(st.session_state["display_items"], merged_summary)
    c1, c2 = st.columns(2)
    c1.metric("Crawl Success Rate", f"{success_rate * 100:.1f}%")
    c2.metric("Summary Accuracy (Estimated)", f"{acc * 100:.1f}%")
    if stats:
        st.json(stats)

    st.divider()
    st.subheader("Export Report")
    if st.session_state["display_items"]:
        word_path = export_word(st.session_state["display_items"], st.session_state["summaries"], "report.docx")
        pdf_path = export_pdf(st.session_state["display_items"], st.session_state["summaries"], "report.pdf")
        with open(word_path, "rb") as f:
            st.download_button("Download Word", f, file_name="report.docx")
        with open(pdf_path, "rb") as f:
            st.download_button("Download PDF", f, file_name="report.pdf")

    st.divider()
    st.subheader("Three Standard Scenarios + Free Search")
    st.markdown(
        "- AI Research Trends: Keywords `LLM RAG Agent` (Recommended sources: arXiv + Hacker News + GitHub)\n"
        "- Graduate Exam Preparation: Keywords `graduate exam math english` (Recommended sources: Google News + Wikipedia + arXiv)\n"
        "- Professional Skills Improvement: Keywords `project management communication analytics`\n"
        "- Free User Search: Any keywords, the system first generates recommended tags, then performs secondary filtering."
    )


if __name__ == "__main__":
    run()
