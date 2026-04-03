# LLM-Assisted Cross-Platform Information Aggregation and Personalized Summarization Tool

**CDS547 Introduction to Large Language Models Course Project**

An intelligent multi-source information aggregation system supporting cross-platform content retrieval, personalized summary generation, and multi-format export.

---

## 🌟 Core Features

- **Cross-Platform Aggregation**: Supports multiple sources including Google News, Bing News, arXiv, Hacker News, GitHub, Wikipedia, StackOverflow, and more
- **Intelligent Processing**: Automatic cleaning, deduplication, and tag classification
- **Personalized Summaries**: Generates customized summaries based on user interest tags and granularity preferences
- **Multi-Format Export**: One-click download in Word and PDF formats
- **Performance Statistics**: Visualized display of crawling success rate and summary accuracy

---

## 🚀 Quick Start

### One-Click Launch (Recommended)

**Windows Users:**
```bash
# Double-click to run
start.bat
```

Or via command line:
```bash
.\start.bat
```

Access: **http://localhost:8501**

---

### Manual Installation and Running

#### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 2. Start Application
```bash
cd llm_info_aggregator
streamlit run app.py --server.port 8501
```

---

## 💻 User Guide

### Three Steps to Generate Summaries

#### 1️⃣ Configure Parameters
Set parameters in the left sidebar:
- **Search Keywords**: e.g., "artificial intelligence", "graduate exam preparation"
- **Source Selection**: Google News RSS, Bing News RSS, arXiv, Hacker News, GitHub Repos, Wikipedia, StackOverflow (recommend at least 3 sources)
- **Items per Source**: 10-60 items
- **Summary Length**: 200-1200 characters

#### 2️⃣ Interest Tag Management
- **Preset Tags**: AI Research, Graduate Exam Prep, Career Skills, etc.
- **Custom Tags**: Support adding, editing, and deleting
- **Example Tags**: `Artificial Intelligence`, `Time Management`, `Data Analysis`

#### 3️⃣ Start Generation
Click the "Start Aggregation and Summarization" button

The system will automatically execute:
1. **Crawl** → Retrieve content from various platforms (approximately 30-60 seconds)
2. **Clean** → Deduplication, standardization, tag classification
3. **Summarize** → Generate personalized summaries by tag

---

### View and Export Results

#### Result Preview
- **Left**: Aggregated content list (title, source, tags, links)
- **Right**: Personalized summaries classified by tags

#### Export Report
Click the "Download Word/PDF Report" button at the bottom to save the complete results.

---

## 🎯 Typical Application Scenarios

### AI Research Tracking
- **Keywords**: `LLM RAG Agent`
- **Sources**: arXiv + Hacker News + GitHub
- **Tags**: Artificial Intelligence

### Graduate Exam Preparation Materials
- **Keywords**: `graduate exam math english`
- **Sources**: Google News + Wikipedia + arXiv
- **Tags**: Graduate Exam

### Career Skill Development
- **Keywords**: `project management communication analytics`
- **Sources**: Google News + Bing News + StackOverflow
- **Tags**: Career Skills

---

## 🔧 Advanced Features

### Domestic LLM API Configuration (Optional)

For higher quality summaries, configure in the sidebar:
- **API Key**: Your secret key
- **Base URL**: e.g., `https://api.deepseek.com/v1`
- **Model**: e.g., `deepseek-chat`

**When not configured**: The system automatically uses local summarization algorithms to ensure stable demonstration.

---

### Tag Management

**Add Tag:**
1. Enter new tag name in the sidebar
2. Click "Add Tag"

**Edit Tag:**
1. Select the tag to edit
2. Enter new name
3. Click "Edit Tag"

**Delete Tag:**
Click the "Delete" button next to the corresponding tag.

---

## 📊 System Architecture

```
llm_info_aggregator/
├── app.py              # Streamlit main interface
├── crawler.py          # Cross-platform crawler
├── llm_core.py         # LLM summary generation
├── utils.py            # Data processing utilities
└── src/
    ├── crawlers/       # Specific crawler implementations
    ├── processing/     # Cleaning, tag classification
    ├── exporters/      # Export functionality
    └── utils/          # Utility functions
```

---

## 👥 Development Team

**CDS547 Intro to Large Language Models - Group Project**