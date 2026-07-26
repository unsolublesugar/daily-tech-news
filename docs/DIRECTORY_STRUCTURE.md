# プロジェクト構造ドキュメント

## ディレクトリ構成

```text
daily-tech-news/
├── fetch_news.py                # メインスクリプト（本番でGitHub Actionsが実行する唯一の実装）
├── daily_tech_news.py            # 新構造移行用エントリーポイント
├── src/                          # Pythonソースコード
│   ├── __init__.py              # メインパッケージ初期化
│   ├── main.py                  # 新構造移行用モジュール（main()は未実装のpassのみ、現状非動作）
│   ├── config/                  # 設定管理
│   │   ├── __init__.py
│   │   └── archive_config.py    # サイト・パス設定（フィードURLはfetch_news.py側で管理）
│   ├── generators/              # 生成エンジン
│   │   ├── __init__.py
│   │   └── archive_generator.py # アーカイブ・インデックス生成
│   ├── templates/               # テンプレート管理
│   │   ├── __init__.py
│   │   └── template_manager.py  # HTML/CSS テンプレート（独自の{{key}}プレースホルダー方式、Jinja2は未使用）
│   └── utils/                   # ユーティリティ（現状未使用）
│       └── __init__.py
├── assets/                       # 静的アセット
│   ├── css/                    # スタイルシート
│   ├── js/                     # JavaScript（app.js）
│   ├── images/                 # 画像ファイル
│   │   └── x-logo/            # Xロゴ
│   ├── favicons/               # ファビコン各種
│   ├── templates/              # HTMLテンプレート断片（header/footer/記事行など）
│   └── partials/               # フッター等の共通パーツ（自動生成、app.jsが起動時にfetch）
├── archives/                     # 生成されたアーカイブ
│   ├── index.html               # アーカイブ一覧（年月タブ＋カレンダー、自動生成）
│   ├── index.md                 # アーカイブ一覧（Markdown版、自動生成）
│   ├── index.json               # 日別サマリーの索引データ（自動生成）
│   └── [年]/[月]/[日付].{md,html}
├── docs/                         # ドキュメント
│   └── DIRECTORY_STRUCTURE.md
├── .claude/                      # Claude Code用ルール・設定
│   └── rules/                   # git-workflow.md / ai-principles.md
├── .github/
│   └── workflows/               # GitHub Actions設定
├── daily_news.md                 # 今日のニュース（自動生成）
├── index.html                    # カード表示版（自動生成）
├── rss.xml                       # RSSフィード（自動生成）
├── requirements.txt              # 依存関係
├── CHANGELOG.md                   # 変更履歴
└── README.md                     # プロジェクト概要
```

## 実行方法

### 本番で使用している実行方法

```bash
python3 fetch_news.py
```

### 新構造移行用エントリーポイント（現状非動作）

```bash
python3 daily_tech_news.py
```

`src/main.py`の`main()`は`pass`のみで未実装のため、現時点では何も生成されない。将来的にこちらへ処理を移す構想があるが、実装が完了するまでは`fetch_news.py`が唯一の実装。

## モジュール構成

### src/config/

- **SiteConfig**: サイト全体の設定管理
- **PathConfig**: パス・URL関連の設定管理
- フィードURL（`FEEDS`辞書）はここではなく`fetch_news.py`内で管理している

### src/generators/

- **ArchiveGenerator**: 日次アーカイブ生成
- **ArchiveIndexGenerator**: インデックスページ生成

### src/templates/

- **TemplateManager**: HTML/CSSテンプレート統一管理（`{{key}}`形式のプレースホルダー置換。Jinja2は使用していない）
- **ContentStructure**: コンテンツ構造化

### src/utils/

- 将来の共通ユーティリティ用（現在は空）

## 変更履歴

過去の大きな変更は[CHANGELOG.md](../CHANGELOG.md)を参照。
