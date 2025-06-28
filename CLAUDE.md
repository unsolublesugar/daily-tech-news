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

## Git Workflow

### Branch Strategy
- **mainブランチ**: 本番環境用、直接コミット禁止
- **featureブランチ**: 新機能開発用 (`feature/機能名`)
- **fixブランチ**: バグ修正用 (`fix/修正内容`)

### Pull Request Creation
プルリクエスト作成時は以下のコマンドを使用:

```bash
# 機能追加の場合
gh pr create --title "✨ 機能名" --assignee unsolublesugar --label enhancement --body "PR説明"

# バグ修正の場合  
gh pr create --title "🐛 修正内容" --assignee unsolublesugar --label bug --body "修正説明"

# ドキュメント更新の場合
gh pr create --title "📚 ドキュメント更新" --assignee unsolublesugar --label documentation --body "更新説明"
```

#### 必須設定項目
- **Assignee**: `unsolublesugar` (必須)
- **Label**: 変更内容に応じて適切なラベルを設定
  - `enhancement`: 新機能追加
  - `bug`: バグ修正
  - `documentation`: ドキュメント更新
  - `refactor`: リファクタリング