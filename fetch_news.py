import feedparser
import datetime

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

def generate_markdown(all_entries, feed_info):
    """取得したエントリーからMarkdownコンテンツを生成する"""
    today = datetime.date.today().isoformat()
    markdown = f"# 毎日のテックニュース ({today})\n\n"
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

if __name__ == "__main__":
    all_entries = {}
    for name, feed_info in FEEDS.items():
        print(f"Fetching entries from {name}...")
        entries = fetch_feed_entries(feed_info["url"])
        all_entries[name] = entries
    
    markdown_content = generate_markdown(all_entries, FEEDS)
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(markdown_content)
        
    print(f"Successfully updated README.md with new feed entries.")