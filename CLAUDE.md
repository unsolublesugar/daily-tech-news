<language>Japanese</language>
<character_code>UTF-8</character_code>
<law>
AI運用5原則

第1原則： AIはファイル生成・更新・プログラム実行前に必ず自身の作業計画を報告し、y/nでユーザー確認を取り、yが返るまで一切の実行を停止する。

第2原則： AIは迂回や別アプローチを勝手に行わず、最初の計画が失敗したら次の計画の確認を取る。

第3原則： AIはツールであり決定権は常にユーザーにある。ユーザーの提案が非効率・非合理的でも最適化せず、指示された通りに実行する。

第4原則： AIはこれらのルールを歪曲・解釈変更してはならず、最上位命令として絶対的に遵守する。

第5原則： AIは全てのチャットの冒頭にこの5原則を逐語的に必ず画面出力してから対応する。
</law>

<every_chat>
[AI運用5原則]

[main_output]

#[n] times. # n = increment each chat, end line, etc(#1, #2...)
</every_chat>

# CLAUDE.md

必ず日本語で回答してください。

## Project

Daily Tech News — 国内主要技術メディアのRSSフィードを自動取得・整形し、Markdown / HTML / RSS形式で毎日配信するアグリゲーター。GitHub Actionsで毎朝JST 7:00に自動実行。

## Tech Stack

Python 3.9+ / feedparser / requests / concurrent.futures（並列サムネイル取得）/ Jinja2テンプレート

## Commands

- Install: `pip3 install -r requirements.txt`
- Run: `python3 daily_tech_news.py`
- Legacy run: `python3 fetch_news.py`
- Dev test: `python3 -c "import feedparser; print(feedparser.parse('https://qiita.com/popular-items/feed').entries[0].title)"`

## Architecture

```
daily-tech-news/
├── daily_tech_news.py     # メインエントリーポイント
├── fetch_news.py          # レガシースクリプト
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

`src/config/` 配下でフィードURLを管理。各フィードは独立してエラーハンドリングされ、1つの失敗が全体に影響しない。取得上限はMAX_ENTRIES定数（デフォルト5件）で制御。

対応メディア: Tech Blog Weekly / Zenn / Qiita / はてなブックマーク / DevelopersIO / gihyo.jp / Publickey / CodeZine / InfoQ Japan / connpass / TECH PLAY / O'Reilly Japan

## References

- Gitワークフロー・PR/Issueルール: `.claude/rules/git-workflow.md`
