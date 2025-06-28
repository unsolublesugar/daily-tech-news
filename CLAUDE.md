# CLAUDE.md

必ず日本語で回答してください。
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based daily tech news aggregator that fetches content from Japanese tech media RSS feeds and generates a daily markdown report. The project aggregates news from:
- Tech Blog Weekly (yamadashy's RSS feed)
- Qiita popular items
- Zenn trending content
- Hatena Bookmark IT section

## Architecture

- **fetch_news.py**: Main script that fetches RSS feeds, processes entries, and generates markdown
- **README.md**: Output file containing the generated daily tech news report
- **requirements.txt**: Python dependencies (feedparser)

## Common Commands

### Setup and Installation
```bash
# Install dependencies
pip3 install -r requirements.txt
```

### Running the Application
```bash
# Generate daily tech news report
python3 fetch_news.py
```

### Development
```bash
# Test RSS feed parsing
python3 -c "import feedparser; print(feedparser.parse('https://qiita.com/popular-items/feed').entries[0].title)"
```

## Key Implementation Details

- Uses `feedparser` library for RSS parsing
- Generates ISO date format for daily reports
- Limits to 10 entries per feed source (MAX_ENTRIES constant)
- Overwrites README.md with each run
- Error handling for failed feed fetches
- UTF-8 encoding for Japanese content support

## Feed Sources Configuration

The FEEDS dictionary in fetch_news.py contains the RSS URLs. Each feed is processed independently with error handling to prevent one failed feed from breaking the entire update process.