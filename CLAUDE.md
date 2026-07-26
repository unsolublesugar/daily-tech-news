<language>Japanese</language>
<character_code>UTF-8</character_code>

# CLAUDE.md

必ず日本語で回答してください。

## Project

Daily Tech News — 国内主要技術メディアのRSSフィードを自動取得・整形し、Markdown / HTML / RSS形式で毎日配信するアグリゲーター。GitHub Actionsで毎朝JST 7:00に自動実行。

## Tech Stack

Python 3.9+ / feedparser / requests / beautifulsoup4 / concurrent.futures（並列サムネイル取得）/ 独自プレースホルダー式テンプレート（`{{key}}`置換、src/templates/template_manager.py。Jinja2は未使用）

## Commands

- Install: `pip3 install -r requirements.txt`
- Run: `python3 fetch_news.py`（本番でGitHub Actionsが実行する唯一の実装）
- Dev test: `python3 -c "import feedparser; print(feedparser.parse('https://qiita.com/popular-items/feed').entries[0].title)"`

## Architecture

```
daily-tech-news/
├── fetch_news.py          # メインスクリプト（本番稼働中の唯一の実装）
├── daily_tech_news.py     # 新構造移行用エントリーポイント（src/main.pyのmain()は未実装のpassのみで現状非動作）
├── src/                   # Pythonモジュール
│   ├── config/            # フィード設定・定数管理
│   ├── generators/        # Markdown / HTML / RSS 生成エンジン
│   ├── templates/         # Jinja2テンプレート管理
│   └── utils/             # 共通ユーティリティ
├── assets/                # CSS / JS / 画像 / HTMLテンプレート
├── archives/              # 過去ニュース（年/月/日付.md）
├── docs/                  # プロジェクトドキュメント
└── .github/workflows/     # GitHub Actions設定
```

**出力ファイル（自動生成）**
- `daily_news.md` — 今日のニュース（Markdown）
- `index.html` — カード表示版（HTML）
- `rss.xml` — RSSフィード

## Feed Sources

フィードURLは`fetch_news.py`内の`FEEDS`辞書で管理（`src/config/`はサイト・パス設定のみを担当）。各フィードは独立してエラーハンドリングされ、1つの失敗が全体に影響しない。取得上限はMAX_ENTRIES定数（デフォルト5件）で制御。

対応メディア: Tech Blog Weekly / Zenn / Qiita / はてなブックマーク / DevelopersIO / gihyo.jp / Publickey / CodeZine / InfoQ Japan / connpass / TECH PLAY / O'Reilly Japan

## References

- Gitワークフロー・PR/Issueルール: `.claude/rules/git-workflow.md`
- AI運用原則: `.claude/rules/ai-principles.md`
