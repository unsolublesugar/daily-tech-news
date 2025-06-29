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

### Development Workflow ⚠️【必須手順】
1. **Issue作成**: 作業開始前に必ずIssueを作成
2. mainブランチに切り替え
3. mainブランチの最新状況をpull
4. Issueに対応するブランチを作成（ブランチ名にIssue番号を含める）
5. 変更を実装・テスト
6. ブランチをリモートにプッシュ
7. **⚠️ Pull Requestを作成（必ずPull Request Creation Rulesを確認）**
8. レビュー・承認後にmainにマージ

### Issue作成ルール

#### 作業開始前の必須手順
```bash
# Issue作成（機能追加の場合）
gh issue create --title "✨ 機能名: 簡潔な説明" --body "詳細な説明" --label enhancement --assignee unsolublesugar

# Issue作成（バグ修正の場合）
gh issue create --title "🐛 バグ: 問題の説明" --body "再現手順と期待する動作" --label bug --assignee unsolublesugar

# Issue作成（ドキュメント更新の場合）
gh issue create --title "📚 ドキュメント: 更新内容" --body "更新理由と詳細" --label documentation --assignee unsolublesugar
```

#### Issue作成時の必須項目
- **タイトル**: 絵文字プレフィックス + 簡潔な説明
- **ラベル**: 作業内容に応じた適切なラベル設定
- **アサイニー**: `unsolublesugar` (必須)
- **本文**: 詳細な説明、受け入れ条件、実装方針など

#### ブランチ作成手順（Issue作成後）
```bash
# mainブランチに切り替え
git checkout main

# 最新状況をpull
git pull origin main

# Issue番号を含むブランチを作成・切り替え
git checkout -b feature/issue-番号-機能名
# または
git checkout -b fix/issue-番号-修正内容

# 例：Issue #13に対応する場合
git checkout -b feature/issue-13-event-deduplication
```

### Pull Request Creation Rules ⚠️【作業実行時必須確認事項】

#### ⚠️ PR作成前の必須チェックリスト
- [ ] タイトルに絵文字プレフィックスが含まれているか
- [ ] タイトル末尾にIssue番号 `(#番号)` が含まれているか  
- [ ] assigneeが `unsolublesugar` に設定されているか
- [ ] 適切なlabelが設定されているか
- [ ] 本文先頭に `Closes #番号` または `Fixes #番号` が記載されているか

#### 基本コマンド（Issue番号を含める）
```bash
# 機能追加の場合（Issue #13に対応）
gh pr create --title "✨ 機能名: 簡潔な説明 (#13)" --assignee unsolublesugar --label enhancement --body "Closes #13\n\n詳細な説明"

# バグ修正の場合（Issue #14に対応）
gh pr create --title "🐛 修正: 問題の説明 (#14)" --assignee unsolublesugar --label bug --body "Fixes #14\n\n修正内容の詳細"

# ドキュメント更新の場合（Issue #15に対応）
gh pr create --title "📚 ドキュメント: 更新内容 (#15)" --assignee unsolublesugar --label documentation --body "Closes #15\n\n更新理由と内容"
```

#### IssueとPRの紐づけ
- **PRタイトル**: 末尾に `(#Issue番号)` を追加
- **PR本文**: 先頭に `Closes #Issue番号` または `Fixes #Issue番号` を記載
- これによりPRマージ時に自動でIssueがクローズされる

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