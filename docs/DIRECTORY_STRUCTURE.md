# プロジェクト構造ドキュメント

## ディレクトリ構成

```
daily-tech-news/
├── src/                          # Pythonソースコード
│   ├── __init__.py              # メインパッケージ初期化
│   ├── main.py                  # メイン処理（旧fetch_news_refactored.py）
│   ├── config/                  # 設定管理
│   │   ├── __init__.py
│   │   └── archive_config.py    # サイト・パス設定
│   ├── generators/              # 生成エンジン
│   │   ├── __init__.py
│   │   └── archive_generator.py # アーカイブ・インデックス生成
│   ├── templates/               # テンプレート管理
│   │   ├── __init__.py
│   │   └── template_manager.py  # HTML/CSS テンプレート
│   └── utils/                   # ユーティリティ
│       └── __init__.py
├── assets/                      # 静的アセット
│   ├── css/                    # スタイルシート（将来拡張）
│   ├── images/                 # 画像ファイル
│   │   └── x-logo/            # 既存Xロゴ
│   └── js/                    # JavaScript（将来拡張）
├── templates/                   # HTMLテンプレート（将来拡張）
├── config/                     # 設定ファイル（将来拡張）
├── tests/                      # テストファイル（将来拡張）
├── docs/                       # ドキュメント
│   └── DIRECTORY_STRUCTURE.md
├── archives/                   # 生成されたアーカイブ
├── daily_tech_news.py         # 新メインエントリーポイント
├── fetch_news.py              # 既存メインスクリプト（互換性維持）
├── requirements.txt           # 依存関係
└── README.md                  # プロジェクト概要
```

## 実行方法

### 新しい構造での実行
```bash
python3 daily_tech_news.py
```

### 既存スクリプトでの実行（互換性維持）
```bash
python3 fetch_news.py
```

## モジュール構成

### src/config/
- **SiteConfig**: サイト全体の設定管理
- **PathConfig**: パス・URL関連の設定管理

### src/generators/
- **ArchiveGenerator**: 日次アーカイブ生成
- **ArchiveIndexGenerator**: インデックスページ生成

### src/templates/
- **TemplateManager**: HTML/CSSテンプレート統一管理
- **ContentStructure**: コンテンツ構造化

### src/utils/
- 将来の共通ユーティリティ用（現在は空）

## 変更履歴

### v2.0.0 - プロジェクト構造改善
- ディレクトリ構造の整理
- モジュール分割による保守性向上
- 既存機能の完全互換性維持
- 将来拡張に向けた基盤整備

### v1.1.0 - リファクタリング
- アーカイブ生成機能の統合
- 重複コード削減
- 設定管理の統一化

### v1.0.0 - 初期版
- 基本的なニュース収集・配信機能
- RSS feed parsing
- HTML/Markdown生成