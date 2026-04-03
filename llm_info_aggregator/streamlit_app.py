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
        "Zhihu": ZhihuCrawler(),
        "News": NewsCrawler(),
        "Academic Paper": ArxivCrawler(),
        "WeChat Official Account": WechatCrawler(),
    }
    articles = []
    for src in selected_sources:
        articles.extend(crawlers[src].crawl(query=query, max_items=max_items))
    return articles


def main():
    st.set_page_config(page_title="LLM Information Aggregation and Summary Tool", layout="wide")
    st.title("LLM-Assisted Cross-Platform Information Aggregation and Personalized Summary Tool")
    st.caption("Process: Crawl -> Clean and Deduplicate -> Tag Classification -> LLM Summary -> Display -> Export")
    ensure_sample_dataset(SAMPLE_FILE, target_size=600)

    tag_manager = TagManager(TAG_FILE)
    tags = tag_manager.load_tags()

    with st.sidebar:
        st.header("Parameter Configuration")
        query = st.text_input("Search keyword", value="Artificial Intelligence")
        sources = st.multiselect(
            "Select information sources",
            options=["WeChat Official Account", "Zhihu", "News", "Academic Paper"],
            default=["Zhihu", "News", "Academic Paper"],
        )
        max_items = st.slider("Max items per source", 5, 50, 20, 5)
        summary_len = st.slider("Max summary length", 150, 1500, 500, 50)
        use_sample = st.toggle("Prioritize loading built-in sample data (500+)", value=True)

        st.divider()
        st.subheader("Interest Tag Management")
        new_tag = st.text_input("Add new tag")
        if st.button("Add tag") and new_tag.strip():
            tags = tag_manager.add_tag(new_tag.strip())
            st.success("Tag added")

        if tags:
            edit_old = st.selectbox("Select tag to edit", options=tags)
            edit_new = st.text_input("New tag name")
            col1, col2 = st.columns(2)
            if col1.button("Edit tag") and edit_new.strip():
                tags = tag_manager.edit_tag(edit_old, edit_new.strip())
                st.success("Tag updated")
            if col2.button("Delete tag"):
                tags = tag_manager.delete_tag(edit_old)
                st.warning("Tag deleted")

        st.write("Current tags:", tags)

    if "articles" not in st.session_state:
        st.session_state.articles = []
    if "summaries" not in st.session_state:
        st.session_state.summaries = {}

    if st.button("Start Aggregation and Summary", type="primary"):
        with st.spinner("Crawling and processing data..."):
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

        st.success(f"Processing completed, total {len(st.session_state.articles)} items.")

    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.subheader("Aggregated Content Preview")
        if st.session_state.articles:
            df = to_dataframe(st.session_state.articles)
            st.dataframe(df[["title", "source_type", "source_name", "tags", "url"]], use_container_width=True)
        else:
            st.info("No data available, click 'Start Aggregation and Summary' to generate.")

    with col_b:
        st.subheader("Personalized Summary")
        if st.session_state.summaries:
            for tag, text in st.session_state.summaries.items():
                st.markdown(f"**{tag}**")
                st.write(text)
        else:
            st.info("No summaries available.")

    st.divider()
    st.subheader("Export")
    if st.session_state.articles:
        word_path = export_word(OUTPUT_DIR / "report.docx", st.session_state.articles, st.session_state.summaries)
        pdf_path = export_pdf(OUTPUT_DIR / "report.pdf", st.session_state.articles, st.session_state.summaries)

        with open(word_path, "rb") as f:
            st.download_button("Download Word Report", f, file_name="report.docx")
        with open(pdf_path, "rb") as f:
            st.download_button("Download PDF Report", f, file_name="report.pdf")

    st.divider()
    st.subheader("Three Scenario Demonstrations")
    st.markdown(
        "- **AI Research**: Keywords `Large Model Agent RAG`, Tag `Artificial Intelligence`\n"
        "- **Graduate Exam Preparation**: Keywords `Graduate Exam Mathematics English Politics`, Tag `Graduate Exam`\n"
        "- **Professional Skills**: Keywords `Project Management Data Analysis Communication`, Tag `Professional Skills`"
    )


if __name__ == "__main__":
    main()
