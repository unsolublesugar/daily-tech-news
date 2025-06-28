import feedparser
import datetime
import os
from pathlib import Path

# 取得するRSSフィードのリスト（ファビコン付き）
FEEDS = {
    "Tech Blog Weekly": {
        "url": "https://yamadashy.github.io/tech-blog-rss-feed/feeds/rss.xml",
        "favicon": "💻"
    },
    "Qiita": {
        "url": "https://qiita.com/popular-items/feed", 
        "favicon": "https://cdn.qiita.com/assets/favicons/public/production-c620d3e403342b1022967ba5e3db1aaa.ico"
    },
    "Zenn": {
        "url": "https://zenn.dev/feed",
        "favicon": "https://zenn.dev/favicon.ico"
    },
    "はてなブックマーク - IT": {
        "url": "http://b.hatena.ne.jp/hotentry/it.rss",
        "favicon": "https://b.hatena.ne.jp/favicon.ico"
    }
}

# 各フィードから取得する記事の件数
MAX_ENTRIES = 10

def fetch_feed_entries(feed_url):
    """指定されたURLからRSSフィードのエントリーを取得する"""
    try:
        feed = feedparser.parse(feed_url)
        return feed.entries
    except Exception as e:
        print(f"Error fetching feed from {feed_url}: {e}")
        return []

def generate_markdown(all_entries, feed_info, date_str):
    """取得したエントリーからMarkdownコンテンツを生成する"""
    markdown = f"# 毎日のテックニュース ({date_str})\n\n"
    markdown += "日本の主要な技術系メディアの最新人気エントリーをお届けします。\n\n---\n"

    for feed_name, entries in all_entries.items():
        favicon = feed_info[feed_name]["favicon"]
        if favicon.startswith("http"):
            # ファビコンURLの場合
            favicon_display = f'<img src="{favicon}" width="16" height="16" alt="{feed_name}">'
        else:
            # 絵文字の場合
            favicon_display = favicon
        markdown += f"## {favicon_display} {feed_name}\n\n"
        if not entries:
            markdown += "記事を取得できませんでした。\n"
        else:
            for entry in entries[:MAX_ENTRIES]:
                title = entry.title
                link = entry.link
                markdown += f"- [{title}]({link})\n"
        
        markdown += "\n---\n"
    
    return markdown

def save_to_archive(content, date_obj):
    """日付別アーカイブファイルとして保存"""
    year = date_obj.year
    month = f"{date_obj.month:02d}"
    date_str = date_obj.isoformat()
    
    # ディレクトリ作成
    archive_dir = Path(f"archives/{year}/{month}")
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # ファイル保存（既存ファイルは上書き）
    archive_file = archive_dir / f"{date_str}.md"
    if archive_file.exists():
        print(f"Overwriting existing archive: {archive_file}")
    else:
        print(f"Creating new archive: {archive_file}")
    
    with open(archive_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    return archive_file

def update_monthly_index(year, month):
    """月別インデックスページを更新"""
    archive_dir = Path(f"archives/{year}/{month:02d}")
    if not archive_dir.exists():
        return
    
    # その月のファイル一覧を取得
    md_files = sorted([f for f in archive_dir.iterdir() if f.suffix == '.md' and f.name != 'index.md'])
    
    # 月別インデックス作成
    index_content = f"# {year}年{month}月のテックニュース\n\n"
    index_content += f"{year}年{month}月に取得したテックニュースの一覧です。\n\n"
    
    for md_file in reversed(md_files):  # 新しい順
        date_str = md_file.stem
        index_content += f"- [{date_str}]({md_file.name})\n"
    
    index_content += f"\n[← {year}年一覧に戻る](../index.md)\n"
    
    with open(archive_dir / "index.md", "w", encoding="utf-8") as f:
        f.write(index_content)

def update_yearly_index(year):
    """年別インデックスページを更新"""
    year_dir = Path(f"archives/{year}")
    if not year_dir.exists():
        return
    
    # その年の月ディレクトリ一覧を取得
    month_dirs = sorted([d for d in year_dir.iterdir() if d.is_dir() and d.name.isdigit()])
    
    # 年別インデックス作成
    index_content = f"# {year}年のテックニュース\n\n"
    index_content += f"{year}年に取得したテックニュースの月別一覧です。\n\n"
    
    for month_dir in reversed(month_dirs):  # 新しい順
        month = int(month_dir.name)
        index_content += f"- [{year}年{month}月]({month_dir.name}/index.md)\n"
    
    index_content += f"\n[← アーカイブ一覧に戻る](../index.md)\n"
    
    with open(year_dir / "index.md", "w", encoding="utf-8") as f:
        f.write(index_content)

def update_archive_index():
    """アーカイブ全体のインデックスページを更新"""
    archives_dir = Path("archives")
    if not archives_dir.exists():
        return
    
    # 年ディレクトリ一覧を取得
    year_dirs = sorted([d for d in archives_dir.iterdir() if d.is_dir() and d.name.isdigit()])
    
    # アーカイブインデックス作成
    index_content = "# テックニュース アーカイブ\n\n"
    index_content += "過去のテックニュースの年別アーカイブです。\n\n"
    
    for year_dir in reversed(year_dirs):  # 新しい順
        year = year_dir.name
        index_content += f"- [{year}年]({year}/index.md)\n"
    
    index_content += f"\n[← メインページに戻る](../README.md)\n"
    
    with open(archives_dir / "index.md", "w", encoding="utf-8") as f:
        f.write(index_content)

def update_readme_with_archive_link(content):
    """README.mdにアーカイブへのリンクを追加"""
    lines = content.split('\n')
    
    # アーカイブリンクを挿入する位置を探す
    insert_index = 2  # タイトルと説明の後
    
    # 既存のアーカイブリンクがあるかチェック
    archive_link_exists = any("📚 [過去のニュースを見る]" in line for line in lines)
    
    if not archive_link_exists:
        archive_link = "\n📚 [過去のニュースを見る](archives/index.md)\n"
        lines.insert(insert_index, archive_link)
    
    return '\n'.join(lines)

if __name__ == "__main__":
    today = datetime.date.today()
    
    all_entries = {}
    for name, feed_info in FEEDS.items():
        print(f"Fetching entries from {name}...")
        entries = fetch_feed_entries(feed_info["url"])
        all_entries[name] = entries
    
    # Markdownコンテンツ生成
    markdown_content = generate_markdown(all_entries, FEEDS, today.isoformat())
    
    # アーカイブに保存
    archive_file = save_to_archive(markdown_content, today)
    print(f"Archived to: {archive_file}")
    
    # インデックスページ更新
    update_monthly_index(today.year, today.month)
    update_yearly_index(today.year)
    update_archive_index()
    
    # README.md更新（アーカイブリンク付き）
    readme_content = update_readme_with_archive_link(markdown_content)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
        
    print(f"Successfully updated README.md and archive structure.")