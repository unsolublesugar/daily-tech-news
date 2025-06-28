import feedparser
import datetime

# 取得するRSSフィードのリスト
FEEDS = {
    "Tech Blog Weekly": "https://yamadashy.github.io/tech-blog-rss-feed/feeds/rss.xml",
    "Qiita": "https://qiita.com/popular-items/feed",
    "Zenn": "https://zenn.dev/feed",
    "はてなブックマーク - IT": "http://b.hatena.ne.jp/hotentry/it.rss"
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

def generate_markdown(all_entries):
    """取得したエントリーからMarkdownコンテンツを生成する"""
    today = datetime.date.today().isoformat()
    markdown = f"# 毎日のテックニュース ({today})\n\n"
    markdown += "日本の主要な技術系メディアの最新人気エントリーをお届けします。\n\n---\n"

    for feed_name, entries in all_entries.items():
        markdown += f"## 📰 {feed_name}\n\n"
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
    for name, url in FEEDS.items():
        print(f"Fetching entries from {name}...")
        entries = fetch_feed_entries(url)
        all_entries[name] = entries
    
    markdown_content = generate_markdown(all_entries)
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(markdown_content)
        
    print(f"Successfully updated README.md with new feed entries.")