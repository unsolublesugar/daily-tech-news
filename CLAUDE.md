<language>Japanese</language>
<character_code>UTF-8</character_code>

# CLAUDE.md

必ず日本語で回答してください。

## Project

Daily Tech News — 国内主要技術メディアのRSSフィードを自動取得・整形し、Markdown / HTML / RSS形式で毎日配信するアグリゲーター。GitHub Actions（`.github/workflows/daily-update.yml`）が毎朝JST 7:00に`fetch_news.py`を実行し、生成物をコミットしてSlackに通知する。

## Tech Stack

Python 3.11（Actionsと同じ版で検証する）/ feedparser / requests / beautifulsoup4 / google-genai（Gemini によるAI要約）/ trafilatura（記事本文抽出）/ concurrent.futures（並列取得）/ 独自プレースホルダー式テンプレート（`{{key}}`置換、`src/templates/template_manager.py`。Jinja2は未使用）。テストフレームワークは未導入。

## Commands

- Install: `pip3 install -r requirements.txt`
- Run: `python3 fetch_news.py`（本番でGitHub Actionsが実行する唯一の実装。ローカルでも動くが生成物を上書きする → 「生成物の扱い」参照）
- Preview: `python3 -m http.server 8000` → `http://localhost:8000/` で `index.html` を目視確認
- Dev test: `python3 -c "import feedparser; print(feedparser.parse('https://qiita.com/popular-items/feed').entries[0].title)"`

## Architecture

```
daily-tech-news/
├── fetch_news.py          # メインスクリプト（FEEDS定義・取得・整形・出力・Slackペイロード生成）
├── daily_tech_news.py     # 新構造移行用エントリーポイント（src/main.pyのmain()は未実装のpassのみで現状非動作）
├── src/
│   ├── ai_summary.py      # AI要約（本文取得→Gemini→data/summaries.jsonにキャッシュ）
│   ├── config/            # サイトURL・パス設定（archive_config.py。フィードURLは持たない）
│   ├── generators/        # アーカイブ・インデックス生成
│   ├── templates/         # template_manager.py（{{key}}置換・HTML組み立て）
│   └── utils/             # 現状未使用
├── prompts/               # AI要約プロンプト（summarize_full.txt / summarize_fallback.txt）
├── data/summaries.json    # AI要約キャッシュ（URLキー、30日で刈り込み。Actionsが自動コミット）
├── assets/                # css / js(app.js) / images / favicons / templates(HTML断片) / partials(自動生成)
├── archives/              # 過去ニュース（年/月/日付.{md,html}、index.*は自動生成）
├── docs/                  # DIRECTORY_STRUCTURE.md ほか
└── .github/workflows/     # daily-update.yml（本番）/ test-branch.yml（フォーク設定の手動テスト）
```

### 生成物の扱い

以下は`fetch_news.py`が生成し、本番ではActionsがコミットする。**手で編集しない。機能開発のPRにも含めない**（差分はコミット前に`git restore`で戻す）。

- `daily_news.md` / `index.html` / `rss.xml` / `archives/` / `assets/partials/`
- `data/summaries.json`（例外: キャッシュ形式の変更など意図がある場合のみPRに含める）
- `slack_message.json` / `thumbnail_cache.json`（gitignore済み）

## Feed Sources

フィードURLは`fetch_news.py`内の`FEEDS`辞書で管理。各フィードは独立してエラーハンドリングされ、1つの失敗が全体に影響しない。取得上限は`MAX_ENTRIES`（既定5件。イベント系は10件）。

- 記事: Tech Blog Weekly / Zenn / Qiita / はてなブックマーク IT（人気・新着）/ DevelopersIO / gihyo.jp / Publickey / CodeZine / InfoQ Japan
- イベント: connpass / TECH PLAY（重複除去・セミナー判定あり）
- 書籍: O'Reilly Japan 近刊

## AI Summary

`src/ai_summary.py`の`attach_ai_summaries()`が**記事フィードのみ**（イベント・書籍は対象外）の各エントリーに`ai_summary`属性（topic / summary_lines / keywords / input_type）を付与する。表示はWeb版（HTML）の展開部のみで、Markdown / RSSには反映しない。

- `LLM_API_KEY`未設定時はスキップして従来のRSS抜粋表示になる。要約の失敗は実行全体を止めない
- LLMはGemini固定。既定モデル`gemini-3.5-flash-lite`（`LLM_MODEL`で差し替え）。無料枠前提で呼び出し間隔・429待機を調整済み
- 本文取得に失敗した記事は`prompts/summarize_fallback.txt`でメタデータのみから簡易要約する
- ローカルで要約を試すとき: `LLM_API_KEY=... MAX_SUMMARIZE_PER_RUN=3 python3 fetch_news.py` のように件数を絞る

## 環境変数

| 変数 | 用途 | 既定 |
|------|------|------|
| `USER_NAME` / `GITHUB_USERNAME` / `REPOSITORY_NAME` / `X_USERNAME` | サイトURL・プロフィール表示（フォーク運用向け。未設定時は`GITHUB_REPOSITORY_OWNER`から自動判定） | — |
| `LLM_API_KEY` | Gemini APIキー。未設定ならAI要約を無効化 | — |
| `LLM_MODEL` | Geminiモデル名 | `gemini-3.5-flash-lite` |
| `MAX_SUMMARIZE_PER_RUN` | 1回の実行で新規要約する上限 | 60 |
| `LLM_MIN_INTERVAL_SECONDS` | LLM呼び出し間隔（秒） | 4.0 |
| `REQUEST_TIMEOUT_SECONDS` | 本文取得タイムアウト（秒） | 15 |
| `SLACK_WEBHOOK_URL` | Actionsのみ。`slack_message.json`を送信 | — |

## 作業の進め方

- 変更前に`fetch_news.py`の該当箇所と、影響する`src/templates/template_manager.py`・`assets/js/app.js`・`assets/templates/`を読む。HTML構造を変えるときはCSS/JSの参照も追従させる
- UI変更は必ずローカルで`python3 fetch_news.py` → `http.server`でブラウザ確認する（`/local-preview`）
- Issue → ブランチ → PR の手順は `.claude/rules/git-workflow.md` に従う（`/start-work`, `/create-pr`, `/release`）
- 迂回や別アプローチを勝手に取らない。詳細は `.claude/rules/ai-principles.md`

## References

- ディレクトリ詳細: `docs/DIRECTORY_STRUCTURE.md`
- Gitワークフロー・PR/Issueルール: `.claude/rules/git-workflow.md`
- AI運用原則: `.claude/rules/ai-principles.md`
