# Daily Tech News

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![RSS](https://img.shields.io/badge/RSS-Available-orange.svg)](https://unsolublesugar.github.io/daily-tech-news/rss.xml)

日本の主要な技術系メディアから最新の人気エントリーを自動収集し、毎日更新するテックニュースアグリゲーターです。

## 📰 今日のニュースを見る

**➡️ [今日のテックニュース](daily_news.md)** | **🎨 [カード表示版](https://unsolublesugar.github.io/daily-tech-news/)** | **📡 [RSS](https://unsolublesugar.github.io/daily-tech-news/rss.xml)**

## ✨ 特徴

- **自動収集**: 国内の主要技術メディアから最新記事を自動取得
- **重複除去**: フィード間の重複記事を自動で除去
- **複数形式**: Markdown、HTML、RSS形式で提供
- **アーカイブ**: 過去のニュースを日付別に保存
- **高速化**: サムネイル並列取得によるパフォーマンス最適化
- **毎日更新**: GitHub Actionsによる自動更新（JST 7:00）

## 📊 対応メディア

| メディア | カテゴリ | 件数 |
|----------|----------|------|
| Tech Blog Weekly | 企業テックブログ | 5件 |
| Zenn | 技術記事・書籍 | 5件 |
| Qiita | 技術記事 | 5件 |
| はてなブックマーク（IT人気・新着） | ソーシャルブックマーク | 各5件 |
| DevelopersIO | クラウド・AWS | 5件 |
| gihyo.jp | 技術情報 | 5件 |
| Publickey | IT業界ニュース | 5件 |
| CodeZine | 開発者向け | 5件 |
| InfoQ Japan | エンタープライズ | 5件 |
| connpass・TECH PLAY | 技術イベント | 各10件 |
| O'Reilly Japan | 技術書籍 | 5件 |

## 🚀 クイックスタート

### 必要環境

- Python 3.8+
- pip

### インストール・実行

```bash
# リポジトリをクローン
git clone https://github.com/unsolublesugar/daily-tech-news.git
cd daily-tech-news

# 依存関係をインストール
pip3 install -r requirements.txt

# ニュース収集を実行
python3 fetch_news.py
```

実行後、以下のファイルが生成されます：

- `daily_news.md` - 今日のニュース（Markdown形式）
- `index.html` - カード表示版（HTML形式）
- `rss.xml` - RSSフィード
- `archives/` - 過去のニュースアーカイブ

## 📁 プロジェクト構成

```
daily-tech-news/
├── fetch_news.py              # メインスクリプト
├── daily_news.md              # 今日のニュース（自動生成）
├── index.html                 # カード表示版（自動生成）
├── rss.xml                    # RSSフィード（自動生成）
├── requirements.txt           # Python依存関係
├── archives/                  # 過去ニュースアーカイブ
│   └── [年]/[月]/[日付].md
├── src/
│   └── templates/            # HTMLテンプレート
└── .github/
    └── workflows/            # GitHub Actions設定
```

## ⚙️ 設定

### フィード設定

`fetch_news.py`の`FEEDS`辞書でRSSフィードを設定できます：

```python
FEEDS = {
    "フィード名": {
        "url": "RSS URL",
        "favicon": "アイコンURL または 絵文字"
    }
}
```

### 記事数制限

`MAX_ENTRIES`定数で各フィードから取得する記事数を調整できます（デフォルト: 5件）。

### ユーザー名設定（フォーク時）

他の開発者がフォークして使用する場合は、以下の手順で設定を変更できます：

#### 1. 環境変数での設定（推奨）

```bash
# 一時的な設定（現在のセッションのみ）
export GITHUB_USERNAME="your-username"
export REPOSITORY_NAME="your-repo-name"
export X_USERNAME="your-x-username"

# スクリプト実行
python3 fetch_news.py
```

#### 2. 永続的な設定

**Linux/macOS の場合:**
```bash
# ~/.bashrc または ~/.zshrc に追加
echo 'export GITHUB_USERNAME="your-username"' >> ~/.bashrc
echo 'export REPOSITORY_NAME="your-repo-name"' >> ~/.bashrc
echo 'export X_USERNAME="your-x-username"' >> ~/.bashrc

# 設定を反映
source ~/.bashrc
```

**Windows の場合:**
```cmd
# 環境変数を永続的に設定
setx GITHUB_USERNAME "your-username"
setx REPOSITORY_NAME "your-repo-name"
setx X_USERNAME "your-x-username"
```

#### 3. GitHub Actions での設定

GitHub Actionsで自動実行する場合は、リポジトリのSecrets設定で環境変数を設定：

1. GitHubリポジトリの「Settings」→「Secrets and variables」→「Actions」
2. 以下のSecretを追加：
   - `USER_NAME`: あなたのGitHubユーザー名
   - `REPOSITORY_NAME`: リポジトリ名
   - `X_USERNAME`: Xユーザー名（@なし）

**注意**: GitHub ActionsではSecret名は`GITHUB_`で始められないため、`USER_NAME`を使用します。

#### 設定例

```bash
# example: ユーザー名が "john" でリポジトリが "my-tech-news" の場合
export GITHUB_USERNAME="john"  # ローカル環境用
export USER_NAME="john"         # GitHub Actions用
export REPOSITORY_NAME="my-tech-news"
export X_USERNAME="john_dev"
```

これにより以下のURLが自動生成されます：
- GitHub Pages: `https://john.github.io/my-tech-news/`
- RSS: `https://john.github.io/my-tech-news/rss.xml`
- GitHub: `https://github.com/john/my-tech-news`

## 🔧 カスタマイズ

### 新しいメディアの追加

1. `FEEDS`辞書に新しいエントリを追加
2. 必要に応じて重複除去ロジックを調整
3. スクリプトを実行してテスト

### テンプレートの変更

HTMLテンプレートは`src/templates/`ディレクトリで管理されています。

## 📈 パフォーマンス

- **並列処理**: サムネイル取得を並列実行
- **キャッシュ**: サムネイルキャッシュによる高速化
- **重複除去**: 効率的なURL重複チェック

## 🤝 コントリビューション

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

詳細は[CLAUDE.md](CLAUDE.md)の開発ワークフローを参照してください。

## 📄 ライセンス

このプロジェクトは[MIT License](LICENSE)の下で公開されています。

## 🙏 謝辞

- 記事を提供していただいている各技術メディアの皆様
- 企業テックブログのRSSフィードを維持・提供していただいている[yamadashy](https://github.com/yamadashy)さん（[企業テックブログRSS](https://yamadashy.github.io/tech-blog-rss-feed/)）

## ✉️ 連絡先

- **作者**: [@unsoluble_sugar](https://x.com/unsoluble_sugar)
- **リポジトリ**: [GitHub](https://github.com/unsolublesugar/daily-tech-news)
- **Issues**: [GitHub Issues](https://github.com/unsolublesugar/daily-tech-news/issues)

本リポジトリの実装は[@unsoluble_sugar](https://x.com/unsoluble_sugar)の指示のもと、すべてClaude Codeによって生成されています。

---

**📱 最新ニュース**: [daily_news.md](daily_news.md) | **🌐 カード表示**: [GitHub Pages](https://unsolublesugar.github.io/daily-tech-news/)