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

## Git Workflow Rules

### Branch Strategy
- **mainブランチ**: 本番環境用、直接コミット完全禁止
- **featureブランチ**: 新機能開発用 (`feature/機能名`)
- **fixブランチ**: バグ修正用 (`fix/修正内容`)

### Development Workflow
1. mainブランチに切り替え
2. mainブランチの最新状況をpull
3. mainブランチから新しいブランチを作成
4. 変更を実装・テスト
5. ブランチをリモートにプッシュ
6. Pull Requestを作成
7. レビュー・承認後にmainにマージ

#### ブランチ作成手順
```bash
# mainブランチに切り替え
git checkout main

# 最新状況をpull
git pull origin main

# 新しいブランチを作成・切り替え
git checkout -b feature/機能名
# または
git checkout -b fix/修正内容
```

### Pull Request Creation Rules

#### 基本コマンド
```bash
# 機能追加の場合
gh pr create --title "✨ 機能名: 簡潔な説明" --assignee unsolublesugar --label enhancement --body "詳細な説明"

# バグ修正の場合  
gh pr create --title "🐛 修正: 問題の説明" --assignee unsolublesugar --label bug --body "修正内容の詳細"

# ドキュメント更新の場合
gh pr create --title "📚 ドキュメント: 更新内容" --assignee unsolublesugar --label documentation --body "更新理由と内容"

# リファクタリングの場合
gh pr create --title "♻️ リファクタリング: 対象範囲" --assignee unsolublesugar --label refactor --body "リファクタリング理由"
```

#### 必須設定項目
- **Assignee**: `unsolublesugar` (必須)
- **Label**: 変更内容に応じて適切なラベルを設定
  - `enhancement`: 新機能追加
  - `bug`: バグ修正  
  - `documentation`: ドキュメント更新
  - `refactor`: リファクタリング
  - `ci`: CI/CD関連の変更

#### タイトル命名規則
- 絵文字プレフィックスを使用
- ✨ 新機能
- 🐛 バグ修正
- 📚 ドキュメント
- ♻️ リファクタリング
- 🔧 設定・環境
- 🚀 パフォーマンス改善

#### PR本文テンプレート
```markdown
## 変更内容
- 具体的な変更点を箇条書き

## 変更理由
- なぜこの変更が必要か

## テスト方法
- 動作確認手順

## 関連Issue
- 関連するIssue番号（あれば）
```