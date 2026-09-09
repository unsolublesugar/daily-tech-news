<language>Japanese</language>
<character_code>UTF-8</character_code>

# CLAUDE.md

必ず日本語で回答してください。

## Project

Daily Tech News — 国内主要技術メディアのRSSフィードを自動取得・整形し、Markdown / HTML / RSS形式で毎日配信するアグリゲーター。GitHub Actionsで毎朝JST 7:00に自動実行。

## Tech Stack

Python 3.11+ / feedparser / requests / beautifulsoup4 / google-genai（Gemini によるAI要約）/ trafilatura（記事本文抽出）/ concurrent.futures（並列取得）/ 独自プレースホルダー式テンプレート（`{{key}}`置換、src/templates/template_manager.py。Jinja2は未使用）

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
│   ├── ai_summary.py      # AI要約（本文取得→Gemini→data/summaries.jsonにキャッシュ）
│   ├── config/            # フィード設定・定数管理
│   ├── generators/        # Markdown / HTML / RSS 生成エンジン
│   ├── templates/         # Jinja2テンプレート管理
│   └── utils/             # 共通ユーティリティ
├── prompts/               # AI要約のプロンプト（本文あり／メタデータのみ）
├── data/summaries.json    # AI要約キャッシュ（URLキー、30日で刈り込み。自動コミット）
├── assets/                # CSS / JS / 画像 / HTMLテンプレート
├── archives/              # 過去ニュース（年/月/日付.md）
├── docs/                  # プロジェクトドキュメント
└── .github/workflows/     # GitHub Actions設定
```

**出力ファイル（自動生成）**
- `daily_news.md` — 今日のニュース（Markdown）
- `index.html` — Web版（HTML）
- `rss.xml` — RSSフィード

## Feed Sources

フィードURLは`fetch_news.py`内の`FEEDS`辞書で管理（`src/config/`はサイト・パス設定のみを担当）。各フィードは独立してエラーハンドリングされ、1つの失敗が全体に影響しない。取得上限はMAX_ENTRIES定数（デフォルト5件）で制御。

## AI Summary

`src/ai_summary.py`が記事フィード（イベント・書籍は対象外）の各エントリーに`ai_summary`属性（topic / summary_lines / keywords / input_type）を付与する。`LLM_API_KEY`未設定時はスキップして従来のRSS抜粋表示になる。LLMはGemini固定（`LLM_MODEL`で差し替え、既定`gemini-3.5-flash-lite`）。本文取得に失敗した記事は`prompts/summarize_fallback.txt`でメタデータのみから簡易要約する。要約の失敗は実行全体を止めない。

対応メディア: Tech Blog Weekly / Zenn / Qiita / はてなブックマーク / DevelopersIO / gihyo.jp / Publickey / CodeZine / InfoQ Japan / connpass / TECH PLAY / O'Reilly Japan

## References

- Gitワークフロー・PR/Issueルール: `.claude/rules/git-workflow.md`
- AI運用原則: `.claude/rules/ai-principles.md`
