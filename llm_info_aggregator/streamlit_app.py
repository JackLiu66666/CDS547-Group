from pathlib import Path
from typing import List

import streamlit as st

from src.crawlers import ArxivCrawler, NewsCrawler, WechatCrawler, ZhihuCrawler
from src.exporters.file_exporter import export_pdf, export_word
from src.llm.summarizer import LLMSummarizer
from src.processing.cleaner import classify_by_tags, deduplicate, group_by_tag, to_dataframe
from src.processing.tags import TagManager
from src.utils.io_utils import load_sample_dataset, save_articles_json
from src.utils.sample_data import ensure_sample_dataset


PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
TAG_FILE = DATA_DIR / "custom_tags.json"
SAMPLE_FILE = DATA_DIR / "sample_dataset.jsonl"
OUTPUT_DIR = PROJECT_ROOT / "outputs"


def run_crawlers(query: str, selected_sources: List[str], max_items: int):
    crawlers = {
        "知乎": ZhihuCrawler(),
        "新闻": NewsCrawler(),
        "学术论文": ArxivCrawler(),
        "公众号": WechatCrawler(),
    }
    articles = []
    for src in selected_sources:
        articles.extend(crawlers[src].crawl(query=query, max_items=max_items))
    return articles


def main():
    st.set_page_config(page_title="LLM信息聚合摘要工具", layout="wide")
    st.title("LLM辅助跨平台信息聚合与个性化摘要工具")
    st.caption("流程: 抓取 -> 清洗去重 -> 标签分类 -> LLM摘要 -> 展示 -> 导出")
    ensure_sample_dataset(SAMPLE_FILE, target_size=600)

    tag_manager = TagManager(TAG_FILE)
    tags = tag_manager.load_tags()

    with st.sidebar:
        st.header("参数配置")
        query = st.text_input("检索关键词", value="人工智能")
        sources = st.multiselect(
            "选择信息源",
            options=["公众号", "知乎", "新闻", "学术论文"],
            default=["知乎", "新闻", "学术论文"],
        )
        max_items = st.slider("每源最大抓取条数", 5, 50, 20, 5)
        summary_len = st.slider("摘要最大字数", 150, 1500, 500, 50)
        use_sample = st.toggle("优先加载内置样本数据（500+）", value=True)

        st.divider()
        st.subheader("兴趣标签管理")
        new_tag = st.text_input("新增标签")
        if st.button("新增标签") and new_tag.strip():
            tags = tag_manager.add_tag(new_tag.strip())
            st.success("标签已新增")

        if tags:
            edit_old = st.selectbox("选择要编辑的标签", options=tags)
            edit_new = st.text_input("新标签名")
            col1, col2 = st.columns(2)
            if col1.button("编辑标签") and edit_new.strip():
                tags = tag_manager.edit_tag(edit_old, edit_new.strip())
                st.success("标签已更新")
            if col2.button("删除标签"):
                tags = tag_manager.delete_tag(edit_old)
                st.warning("标签已删除")

        st.write("当前标签:", tags)

    if "articles" not in st.session_state:
        st.session_state.articles = []
    if "summaries" not in st.session_state:
        st.session_state.summaries = {}

    if st.button("开始聚合与摘要", type="primary"):
        with st.spinner("正在抓取和处理数据..."):
            crawled = run_crawlers(query, sources, max_items) if sources else []
            sample = load_sample_dataset(SAMPLE_FILE) if use_sample else []
            combined = crawled + sample[: min(300, len(sample))]
            cleaned = deduplicate(combined)
            classified = classify_by_tags(cleaned, tags)
            grouped = group_by_tag(classified)
            summarizer = LLMSummarizer()
            summaries = summarizer.summarize(grouped, max_chars=summary_len)

            st.session_state.articles = classified
            st.session_state.summaries = summaries
            save_articles_json(OUTPUT_DIR / "latest_articles.json", classified)

        st.success(f"处理完成，总计 {len(st.session_state.articles)} 条内容。")

    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.subheader("聚合内容预览")
        if st.session_state.articles:
            df = to_dataframe(st.session_state.articles)
            st.dataframe(df[["title", "source_type", "source_name", "tags", "url"]], use_container_width=True)
        else:
            st.info("暂无数据，点击“开始聚合与摘要”生成。")

    with col_b:
        st.subheader("个性化摘要")
        if st.session_state.summaries:
            for tag, text in st.session_state.summaries.items():
                st.markdown(f"**{tag}**")
                st.write(text)
        else:
            st.info("暂无摘要。")

    st.divider()
    st.subheader("导出")
    if st.session_state.articles:
        word_path = export_word(OUTPUT_DIR / "report.docx", st.session_state.articles, st.session_state.summaries)
        pdf_path = export_pdf(OUTPUT_DIR / "report.pdf", st.session_state.articles, st.session_state.summaries)

        with open(word_path, "rb") as f:
            st.download_button("下载 Word 报告", f, file_name="report.docx")
        with open(pdf_path, "rb") as f:
            st.download_button("下载 PDF 报告", f, file_name="report.pdf")

    st.divider()
    st.subheader("三大场景演示")
    st.markdown(
        "- **AI研究**：关键词 `大模型 Agent RAG`，标签 `人工智能`。\n"
        "- **考研备考**：关键词 `考研 数学 英语 政治`，标签 `考研`。\n"
        "- **职场技能**：关键词 `项目管理 数据分析 沟通`，标签 `职场技能`。"
    )


if __name__ == "__main__":
    main()
