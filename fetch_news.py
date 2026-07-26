import feedparser
import datetime
import os
import sys
from pathlib import Path
from xml.dom import minidom
import xml.etree.ElementTree as ET
import time
import re
import json
from urllib.parse import urlparse, urlunparse, urlencode, parse_qsl

# srcディレクトリをPythonパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 設定のインポート
from config.archive_config import DEFAULT_SITE_CONFIG, is_article_feed
from generators.archive_generator import ArchiveGenerator

# 取得するRSSフィードのリスト
FEEDS = {
    "Tech Blog Weekly": "https://yamadashy.github.io/tech-blog-rss-feed/feeds/rss.xml",
    "Zenn": "https://zenn.dev/feed",
    "Qiita": "https://qiita.com/popular-items/feed",
    "はてなブックマーク - IT（人気）": "http://b.hatena.ne.jp/hotentry/it.rss",
    "はてなブックマーク - IT（新着）": "https://b.hatena.ne.jp/entrylist/it.rss",
    "DevelopersIO": "https://dev.classmethod.jp/feed/",
    "gihyo.jp": "https://gihyo.jp/dev/feed/rss2",
    "Publickey": "https://www.publickey1.jp/atom.xml",
    "CodeZine": "https://codezine.jp/rss/new/20/index.xml",
    "InfoQ Japan": "https://feed.infoq.com/jp",
    "connpass - イベント": "https://connpass.com/explore/ja.atom",
    "TECH PLAY - イベント": "https://rss.techplay.jp/event/w3c-rss-format/rss.xml",
    "O'Reilly Japan - 近刊": "https://www.oreilly.co.jp/catalog/soon.xml"
}

# 除外するドメインのリスト
EXCLUDED_DOMAINS = {
    'anond.hatelabo.jp': 'hatena anonymous diary',
    'togetter.com': 'togetter'
}

# 各フィードから取得する記事の件数
MAX_ENTRIES = 5

_TRACKING_PARAMS = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "ref", "fbclid", "gclid",
})

def normalize_url(url):
    """URLを正規化して重複検出の精度を向上させる。

    - トラッキングパラメータ（utm_*、ref、fbclid、gclid）を除去
    - スキームを https に統一（http -> https）
    - パス末尾のスラッシュを除去
    - 元のURLは変更しない（比較用のみ）
    """
    if not url:
        return url
    try:
        parsed = urlparse(url)
        scheme = "https" if parsed.scheme == "http" else parsed.scheme
        path = parsed.path.rstrip("/") or "/"
        filtered_query = urlencode(
            [(k, v) for k, v in parse_qsl(parsed.query)
             if k.lower() not in _TRACKING_PARAMS]
        )
        return urlunparse((scheme, parsed.netloc, path, parsed.params, filtered_query, ""))
    except Exception:
        return url

def filter_entries_by_domain(entries, domain, label):
    filtered_entries = []
    excluded_count = 0
    
    for entry in entries:
        if hasattr(entry, 'link') and domain in entry.link:
            excluded_count += 1
            continue
        filtered_entries.append(entry)
    
    if excluded_count > 0:
        print(f"Excluded {excluded_count} {label} entries")
    
    return filtered_entries

def extract_author_info(entry):
    """RSSエントリーから著者情報を抽出する"""
    author = None
    
    # 複数のフィールドから著者情報を取得を試行
    if hasattr(entry, 'author') and entry.author:
        author = entry.author.strip()
    elif hasattr(entry, 'author_detail') and entry.author_detail and entry.author_detail.get('name'):
        author = entry.author_detail['name'].strip()
    elif hasattr(entry, 'authors') and entry.authors and len(entry.authors) > 0:
        first_author = entry.authors[0]
        if isinstance(first_author, dict) and first_author.get('name'):
            author = first_author['name'].strip()
        elif hasattr(first_author, 'name'):
            author = first_author.name.strip()
    
    # 著者情報があれば、長すぎる場合は短縮処理
    if author:
        # O'Reilly Japan等の長い著者情報の短縮処理
        if len(author) > 50:  # 50文字を超える場合
            # "著者名　著 訳者名　訳" パターンの処理
            if "　著" in author:
                author = author.split("　著")[0]
            # カンマ区切りの複数著者の場合、最初の2名まで
            elif "、" in author:
                authors = author.split("、")
                if len(authors) > 2:
                    author = "、".join(authors[:2]) + "他"
                else:
                    author = "、".join(authors[:2])
            # それでも長い場合は前半50文字+...
            if len(author) > 50:
                author = author[:47] + "..."
    
    return author

def fetch_feed_entries(feed_url):
    """指定されたURLからRSSフィードのエントリーを取得する"""
    try:
        feed = feedparser.parse(feed_url)
        
        # 各エントリに著者情報を追加
        for entry in feed.entries:
            entry.author_info = extract_author_info(entry)
        
        return feed.entries
    except Exception as e:
        print(f"Error fetching feed from {feed_url}: {e}")
        return []

def deduplicate_events(entries, target_count=10):
    """イベント系エントリーの重複を除去（シリーズ番号違いを統合）し、目標件数を確保"""
    if not entries:
        return entries
    
    # イベント名の基底部分を抽出するパターン
    patterns = [
        r'^(.+?)\s*#\d+.*$',  # "朝活もくもく会 #19" -> "朝活もくもく会"
        r'^(.+?)\s*第\d+回.*$',  # "第5回勉強会" -> "勉強会" 
        r'^(.+?)\s*Vol\.\d+.*$',  # "勉強会 Vol.3" -> "勉強会"
        r'^(.+?)\s*\(\d+\).*$',  # "勉強会(3)" -> "勉強会"
        r'^(.+?)\s*-\s*\d+.*$',  # "勉強会 - 5" -> "勉強会"
    ]
    
    # エントリーを基底名でグループ化
    event_groups = {}
    
    for entry in entries:
        title = entry.title.strip()
        base_name = title
        
        # パターンマッチングで基底名を抽出
        for pattern in patterns:
            match = re.match(pattern, title)
            if match:
                base_name = match.group(1).strip()
                break
        
        # 基底名でグループ化（最新のエントリーを優先）
        if base_name not in event_groups:
            event_groups[base_name] = entry
        else:
            # 既存エントリーより新しい場合は置き換え
            existing_date = getattr(event_groups[base_name], 'published_parsed', None)
            current_date = getattr(entry, 'published_parsed', None)
            
            if current_date and existing_date:
                if current_date > existing_date:
                    event_groups[base_name] = entry
            elif current_date and not existing_date:
                event_groups[base_name] = entry
    
    # グループ化されたエントリーを返す（元の順序を保持）
    deduplicated = []
    seen_bases = set()
    
    for entry in entries:
        title = entry.title.strip()
        base_name = title
        
        for pattern in patterns:
            match = re.match(pattern, title)
            if match:
                base_name = match.group(1).strip()
                break
        
        if base_name not in seen_bases:
            deduplicated.append(event_groups[base_name])
            seen_bases.add(base_name)
            
            # 目標件数に達したら終了
            if len(deduplicated) >= target_count:
                break
    
    return deduplicated

def deduplicate_urls_across_feeds(all_entries):
    """フィード間でのURL重複を除去し、補填を行う（PRIORITY_FEEDS順で処理）"""
    seen_urls = set()
    deduplicated_feeds = {}
    dedup_stats = {"total_removed": 0, "norm_caught": 0, "by_feed": {}}
    
    # PRIORITY_FEEDSの順序でフィードを処理
    from src.config.archive_config import DEFAULT_SITE_CONFIG
    priority_feeds = DEFAULT_SITE_CONFIG.PRIORITY_FEEDS
    
    # PRIORITY_FEEDSに含まれるフィードから処理
    processed_feeds = set()
    for feed_name in priority_feeds:
        if feed_name in all_entries:
            processed_feeds.add(feed_name)
            entries = all_entries[feed_name]
            
            if not entries:
                deduplicated_feeds[feed_name] = entries
                continue
                
            # イベントフィードかどうかで目標件数を決定
            target_count = 10 if "イベント" in feed_name else 5
            
            # URL重複除去（正規化URLで比較）
            unique_entries = []
            removed_count = 0
            norm_caught_feed = 0
            for entry in entries:
                if not hasattr(entry, 'link'):
                    unique_entries.append(entry)
                    continue
                norm = normalize_url(entry.link)
                if norm not in seen_urls:
                    seen_urls.add(norm)
                    unique_entries.append(entry)
                    if len(unique_entries) >= target_count:
                        break
                else:
                    removed_count += 1
                    if hasattr(entry, 'title'):
                        print(f"重複除去: [{feed_name}] {entry.title}")
                        print(f"  URL: {entry.link}")
                        if norm != entry.link:
                            print(f"  正規化URL: {norm}  ← 正規化による検出")
                            norm_caught_feed += 1

            # イベントフィードの場合はさらにイベント重複除去を適用
            if "イベント" in feed_name:
                unique_entries = deduplicate_events(unique_entries, target_count)

            deduplicated_feeds[feed_name] = unique_entries
            dedup_stats["by_feed"][feed_name] = removed_count
            dedup_stats["total_removed"] += removed_count
            dedup_stats["norm_caught"] += norm_caught_feed

    # PRIORITY_FEEDSに含まれていないフィードを処理
    for feed_name, entries in all_entries.items():
        if feed_name not in processed_feeds:
            if not entries:
                deduplicated_feeds[feed_name] = entries
                continue

            # イベントフィードかどうかで目標件数を決定
            target_count = 10 if "イベント" in feed_name else 5

            # URL重複除去（正規化URLで比較）
            unique_entries = []
            removed_count = 0
            norm_caught_feed = 0
            for entry in entries:
                if not hasattr(entry, 'link'):
                    unique_entries.append(entry)
                    continue
                norm = normalize_url(entry.link)
                if norm not in seen_urls:
                    seen_urls.add(norm)
                    unique_entries.append(entry)
                    if len(unique_entries) >= target_count:
                        break
                else:
                    removed_count += 1
                    if hasattr(entry, 'title'):
                        print(f"重複除去: [{feed_name}] {entry.title}")
                        print(f"  URL: {entry.link}")
                        if norm != entry.link:
                            print(f"  正規化URL: {norm}  ← 正規化による検出")
                            norm_caught_feed += 1

            # イベントフィードの場合はさらにイベント重複除去を適用
            if "イベント" in feed_name:
                unique_entries = deduplicate_events(unique_entries, target_count)

            deduplicated_feeds[feed_name] = unique_entries
            dedup_stats["by_feed"][feed_name] = removed_count
            dedup_stats["total_removed"] += removed_count
            dedup_stats["norm_caught"] += norm_caught_feed

    # 重複除去統計を出力
    if dedup_stats["total_removed"] > 0:
        norm_caught = dedup_stats["norm_caught"]
        exact_caught = dedup_stats["total_removed"] - norm_caught
        print(f"URL重複除去統計: 合計{dedup_stats['total_removed']}件を除去")
        print(f"  うち正規化による検出: {norm_caught}件 / 完全一致による検出: {exact_caught}件")
        for feed_name, removed_count in dedup_stats["by_feed"].items():
            if removed_count > 0:
                print(f"  {feed_name}: {removed_count}件")
    
    return deduplicated_feeds

_archive_generator = ArchiveGenerator()


def normalize_title_for_dedup(title):
    """タイトル比較用の正規化（空白・記号を落として先頭40文字）"""
    if not title:
        return ""
    normalized = re.sub(r'<[^>]+>', '', title)
    normalized = re.sub(r'[\s　!-/:-@\[-`{-~！-／：-＠［-｀｛-～、。「」【】（）]', '', normalized)
    return normalized.lower()[:40]


def count_cross_feed_mentions(all_entries):
    """フィード間で何メディアに出現したかを数える

    ハイライト選定に使う。フィード間のURL重複除去を「行う前」の
    全エントリを対象にしないと重複情報そのものが消えてしまうため、
    deduplicate_urls_across_feeds() より先に呼ぶこと。

    Returns:
        dict: 記事URL -> 出現メディア数（1以上）
    """
    url_feeds = {}
    title_feeds = {}

    for feed_name, entries in all_entries.items():
        if not is_article_feed(feed_name):
            continue
        for entry in entries:
            link = getattr(entry, 'link', None)
            if not link:
                continue
            url_feeds.setdefault(normalize_url(link), set()).add(feed_name)
            title_key = normalize_title_for_dedup(getattr(entry, 'title', ''))
            if title_key:
                title_feeds.setdefault(title_key, set()).add(feed_name)

    mention_counts = {}
    for feed_name, entries in all_entries.items():
        if not is_article_feed(feed_name):
            continue
        for entry in entries:
            link = getattr(entry, 'link', None)
            if not link:
                continue
            feeds = set(url_feeds.get(normalize_url(link), set()))
            title_key = normalize_title_for_dedup(getattr(entry, 'title', ''))
            if title_key:
                feeds |= title_feeds.get(title_key, set())
            mention_counts[link] = max(1, len(feeds))

    multi = sum(1 for count in mention_counts.values() if count > 1)
    if multi:
        print(f"複数メディアで言及されている記事: {multi}件")

    return mention_counts


def generate_html(all_entries, date_obj, mention_counts=None):
    """トップページ（記事／イベント／書籍の3タブ）のHTMLを生成する"""
    return _archive_generator.build_page(
        all_entries, date_obj, mention_counts, is_archive=False
    )

def generate_markdown(all_entries, date_str):
    """取得したエントリーからMarkdownコンテンツを生成する"""
    markdown = f"# 今日のテックニュース ({date_str})\n\n"
    markdown += f"""📚 [過去のニュースを見る](archives/index.md) | 🎨 [カード表示版を見る]({DEFAULT_SITE_CONFIG.site_url}) | 📡 [RSSフィードを購読]({DEFAULT_SITE_CONFIG.rss_url})

日本の主要な技術系メディアの最新人気エントリーをお届けします。

※毎日JST 7:00に自動更新

## 🎨 カード表示版もあります

GitHub Pages版では各記事がカード形式で見やすく表示されます：  
{DEFAULT_SITE_CONFIG.site_url}

---
"""

    for feed_name, entries in all_entries.items():
        markdown += f"## {feed_name}\n\n"
        if not entries:
            markdown += "記事を取得できませんでした。\n"
        else:
            # エントリーはすでにURL重複除去済み
            for entry in entries:
                title = entry.title
                link = entry.link
                
                # シンプルなリンク形式で表示
                markdown += f"- [{title}]({link})\n"
        
        markdown += "\n\n---\n"
    
    markdown += "## License\n\nThis project is licensed under the [MIT License](LICENSE).\n"
    
    return markdown

def generate_archive_markdown(all_entries, date_str):
    """アーカイブ用のMarkdownコンテンツを生成する（相対パス修正版）"""
    markdown = f"# 今日のテックニュース ({date_str})\n\n"
    markdown += f"""📚 [過去のニュースを見る](../../daily_news.md) | 🎨 [カード表示版を見る]({DEFAULT_SITE_CONFIG.site_url}) | 📡 [RSSフィードを購読]({DEFAULT_SITE_CONFIG.rss_url})

日本の主要な技術系メディアの最新人気エントリーをお届けします。

## 🎨 カード表示版もあります

GitHub Pages版では各記事がカード形式で見やすく表示されます：  
{DEFAULT_SITE_CONFIG.site_url}

---
"""

    for feed_name, entries in all_entries.items():
        markdown += f"## {feed_name}\n\n"
        if not entries:
            markdown += "記事を取得できませんでした。\n"
        else:
            # エントリーはすでにURL重複除去済み
            for entry in entries:
                title = entry.title
                link = entry.link
                
                # シンプルなリンク形式で表示
                markdown += f"- [{title}]({link})\n"
        
        markdown += "\n\n---\n"
    
    markdown += "## License\n\nThis project is licensed under the [MIT License](LICENSE).\n"
    
    return markdown

def generate_archive_html(all_entries, date_obj, mention_counts=None):
    """アーカイブ用（archives/YYYY/MM/）のHTMLを生成する"""
    return _archive_generator.build_page(
        all_entries, date_obj, mention_counts, is_archive=True, depth=3
    )

def save_to_archive(all_entries, date_obj, mention_counts=None):
    """日付別アーカイブファイルとして保存（MarkdownとHTML両方）"""
    year = date_obj.year
    month = f"{date_obj.month:02d}"
    date_str = date_obj.isoformat()
    
    # ディレクトリ作成
    archive_dir = Path(f"archives/{year}/{month}")
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # Markdown版
    md_content = generate_archive_markdown(all_entries, date_str)
    archive_file = archive_dir / f"{date_str}.md"
    if archive_file.exists():
        print(f"Overwriting existing archive: {archive_file}")
    else:
        print(f"Creating new archive: {archive_file}")
    
    with open(archive_file, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    # HTML版
    html_content = generate_archive_html(all_entries, date_obj, mention_counts)
    html_file = archive_dir / f"{date_str}.html"
    
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"Generated archive files: {archive_file} and {html_file}")
    
    return archive_file

def update_monthly_index(year, month):
    """月別インデックスページを更新（MarkdownとHTML両方）"""
    archive_dir = Path(f"archives/{year}/{month:02d}")
    if not archive_dir.exists():
        return
    
    # その月のファイル一覧を取得
    md_files = sorted([f for f in archive_dir.iterdir() if f.suffix == '.md' and f.name != 'index.md'])
    
    # Markdown版
    md_content = f"# {year}年{month}月のテックニュース\n\n"
    md_content += f"{year}年{month}月に取得したテックニュースの一覧です。\n\n"
    
    for md_file in reversed(md_files):  # 新しい順
        date_str = md_file.stem
        md_content += f"- [{date_str}]({md_file.name})\n"
    
    md_content += f"\n[← {year}年一覧に戻る](../index.md)\n"
    
    with open(archive_dir / "index.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    
    # HTML版
    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{year}年{month}月のテックニュース</title>
    
    <!-- OGP Tags -->
    <meta property="og:title" content="{year}年{month}月のテックニュース">
    <meta property="og:description" content="日本の主要な技術系メディアの最新人気エントリーを毎日お届けします。">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{DEFAULT_SITE_CONFIG.site_url}">
    <meta property="og:image" content="{DEFAULT_SITE_CONFIG.og_image_url}">
    <meta property="og:site_name" content="今日のテックニュース">
    
    <!-- Twitter Card Tags -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:creator" content="@unsoluble_sugar">
    <meta name="twitter:title" content="{year}年{month}月のテックニュース">
    <meta name="twitter:description" content="日本の主要な技術系メディアの最新人気エントリーを毎日お届けします。">
    <meta name="twitter:image" content="{DEFAULT_SITE_CONFIG.og_image_url}">
    
    <!-- Favicon Links -->
    <link rel="apple-touch-icon" sizes="180x180" href="../../../assets/favicons/apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="32x32" href="../../../assets/favicons/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="../../../assets/favicons/favicon-16x16.png">
    <link rel="manifest" href="../../../assets/favicons/site.webmanifest">
    <link rel="shortcut icon" href="../../../assets/favicons/favicon.ico">
    
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{
            color: #1f2328;
        }}
        ul {{
            list-style-type: disc;
            padding-left: 2em;
        }}
        li {{
            margin: 8px 0;
        }}
        a {{
            color: #0969da;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .back-link {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e1e5e9;
        }}
    </style>
</head>
<body>
    <h1>{year}年{month}月のテックニュース</h1>
    
    <p>{year}年{month}月に取得したテックニュースの一覧です。</p>
    
    <ul>"""
    
    for md_file in reversed(md_files):  # 新しい順
        date_str = md_file.stem
        html_content += f'\n        <li><a href="{date_str}.html">{date_str}</a></li>'
    
    html_content += f"""
    </ul>
    
    <div class="back-link">
        <p><a href="../index.html">← {year}年一覧に戻る</a></p>
    </div>
</body>
</html>"""
    
    with open(archive_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

def update_yearly_index(year):
    """年別インデックスページを更新（MarkdownとHTML両方）"""
    year_dir = Path(f"archives/{year}")
    if not year_dir.exists():
        return
    
    # その年の月ディレクトリ一覧を取得
    month_dirs = sorted([d for d in year_dir.iterdir() if d.is_dir() and d.name.isdigit()])
    
    # Markdown版
    md_content = f"# {year}年のテックニュース\n\n"
    md_content += f"{year}年に取得したテックニュースの月別一覧です。\n\n"
    
    for month_dir in reversed(month_dirs):  # 新しい順
        month = int(month_dir.name)
        md_content += f"- [{year}年{month}月]({month_dir.name}/index.md)\n"
    
    md_content += f"\n[← アーカイブ一覧に戻る](../index.md)\n"
    
    with open(year_dir / "index.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    
    # HTML版
    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{year}年のテックニュース</title>
    
    <!-- OGP Tags -->
    <meta property="og:title" content="{year}年のテックニュース">
    <meta property="og:description" content="日本の主要な技術系メディアの最新人気エントリーを毎日お届けします。">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{DEFAULT_SITE_CONFIG.site_url}">
    <meta property="og:image" content="{DEFAULT_SITE_CONFIG.og_image_url}">
    <meta property="og:site_name" content="今日のテックニュース">
    
    <!-- Twitter Card Tags -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:creator" content="@unsoluble_sugar">
    <meta name="twitter:title" content="{year}年のテックニュース">
    <meta name="twitter:description" content="日本の主要な技術系メディアの最新人気エントリーを毎日お届けします。">
    <meta name="twitter:image" content="{DEFAULT_SITE_CONFIG.og_image_url}">
    
    <!-- Favicon Links -->
    <link rel="apple-touch-icon" sizes="180x180" href="../../assets/favicons/apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="32x32" href="../../assets/favicons/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="../../assets/favicons/favicon-16x16.png">
    <link rel="manifest" href="../../assets/favicons/site.webmanifest">
    <link rel="shortcut icon" href="../../assets/favicons/favicon.ico">
    
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{
            color: #1f2328;
        }}
        ul {{
            list-style-type: disc;
            padding-left: 2em;
        }}
        li {{
            margin: 8px 0;
        }}
        a {{
            color: #0969da;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .back-link {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e1e5e9;
        }}
    </style>
</head>
<body>
    <h1>{year}年のテックニュース</h1>
    
    <p>{year}年に取得したテックニュースの月別一覧です。</p>
    
    <ul>"""
    
    for month_dir in reversed(month_dirs):  # 新しい順
        month = int(month_dir.name)
        html_content += f'\n        <li><a href="{month_dir.name}/index.html">{year}年{month}月</a></li>'
    
    html_content += f"""
    </ul>
    
    <div class="back-link">
        <p><a href="../index.html">← アーカイブ一覧に戻る</a></p>
    </div>
</body>
</html>"""
    
    with open(year_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

def generate_missing_html_archives():
    """既存のMarkdownアーカイブファイルに対応するHTMLファイルが存在しない場合に生成する"""
    archives_dir = Path("archives")
    if not archives_dir.exists():
        return
    
    # 全てのMarkdownアーカイブファイルを検索
    md_files = list(archives_dir.glob("**/????-??-??.md"))
    
    for md_file in md_files:
        html_file = md_file.with_suffix('.html')
        
        # HTMLファイルが存在しない場合のみ生成
        if not html_file.exists():
            print(f"Generating missing HTML archive: {html_file}")
            
            # Markdownファイルからコンテンツを読み取り、簡易的にHTMLに変換
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    md_content = f.read()
                
                # 日付を抽出
                date_match = re.search(r'# 今日のテックニュース \((\d{4}-\d{2}-\d{2})\)', md_content)
                if date_match:
                    date_str = date_match.group(1)
                    
                    # 簡易的なHTML生成（完全な記事リスト無しでも基本構造を生成）
                    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>今日のテックニュース ({date_str})</title>
    
    <!-- OGP Tags -->
    <meta property="og:title" content="今日のテックニュース ({date_str})">
    <meta property="og:description" content="日本の主要な技術系メディアの最新人気エントリーを毎日お届けします。">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{DEFAULT_SITE_CONFIG.site_url}">
    <meta property="og:image" content="{DEFAULT_SITE_CONFIG.og_image_url}">
    <meta property="og:site_name" content="今日のテックニュース">
    
    <!-- Twitter Card Tags -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:site" content="@unsoluble_sugar">
    
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1, h2 {{
            color: #1f2328;
        }}
        a {{
            color: #0969da;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .rss-info {{
            background: #f6f8fa;
            padding: 16px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .footer {{
            margin-top: 40px;
            padding: 20px 0;
            border-top: 1px solid #e1e5e9;
            text-align: center;
            font-size: 14px;
            color: #656d76;
        }}
        .footer a {{
            color: #0969da;
            text-decoration: none;
        }}
        .footer a:hover {{
            text-decoration: underline;
        }}
        ul {{
            line-height: 1.8;
        }}
    </style>
</head>
<body>
    <h1>今日のテックニュース ({date_str})</h1>
    
    <p>📚 <a href="../../index.html">過去のニュースを見る</a> | 📡 <a href="{DEFAULT_SITE_CONFIG.rss_url}">RSSフィードを購読</a></p>
    
    <p>日本の主要な技術系メディアの最新人気エントリーをお届けします。</p>
    
    <div class="rss-info">
        <p>毎日JST 7:00に自動更新</p>
    </div>
    
    <hr>
"""
                    
                    # Markdownの内容を簡易的にHTMLに変換
                    lines = md_content.split('\n')
                    in_list = False
                    current_section = None
                    
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                            
                        # セクションヘッダー
                        if line.startswith('## ') and not line.startswith('## License'):
                            if in_list:
                                html_content += "    </ul>\n    <hr>\n"
                                in_list = False
                            
                            section_title = line[3:].strip()
                            html_content += f"    <h2>{section_title}</h2>\n"
                            current_section = section_title
                            
                        # リスト項目
                        elif line.startswith('- [') and current_section and 'License' not in current_section:
                            if not in_list:
                                html_content += "    <ul>\n"
                                in_list = True
                            
                            # リンクを抽出
                            link_match = re.match(r'- \[([^\]]+)\]\(([^)]+)\)', line)
                            if link_match:
                                title, url = link_match.groups()
                                html_content += f'        <li><a href="{url}">{title}</a></li>\n'
                    
                    if in_list:
                        html_content += "    </ul>\n    <hr>\n"
                    
                    html_content += """
    <div class="footer">
        <p>📡 <a href="{DEFAULT_SITE_CONFIG.rss_url}">RSSフィードを購読</a></p>
        <p>🚀 <a href="https://unsolublesugar.github.io/portfolio/" target="_blank" rel="noopener">{DEFAULT_SITE_CONFIG.profile_display_name}</a> |
        📁 <a href="{DEFAULT_SITE_CONFIG.github_repo_url}" target="_blank" rel="noopener">GitHub Repository</a></p>
    </div>
</body>
</html>"""
                    
                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                        
            except Exception as e:
                print(f"Error generating HTML for {md_file}: {e}")

def update_archive_index():
    """アーカイブ全体のインデックスページを更新（MarkdownとHTML両方）"""
    archives_dir = Path("archives")
    if not archives_dir.exists():
        return
    
    # 既存のMarkdownファイルに対応するHTMLファイルを生成
    generate_missing_html_archives()
    
    # 年ディレクトリ一覧を取得
    year_dirs = sorted([d for d in archives_dir.iterdir() if d.is_dir() and d.name.isdigit()])
    
    # Markdown版（README.mdからの遷移用）
    md_content = "# テックニュース アーカイブ\n\n"
    md_content += "過去のテックニュースの年別アーカイブです。\n\n"
    
    for year_dir in reversed(year_dirs):  # 新しい順
        year = year_dir.name
        md_content += f"- [{year}年]({year}/index.md)\n"
    
    md_content += f"\n[← メインページに戻る](../daily_news.md)\n"
    with open(archives_dir / "index.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    
    # HTML版（index.htmlからの遷移用）
    html_content = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>テックニュース アーカイブ</title>
    
    <!-- OGP Tags -->
    <meta property="og:title" content="テックニュース アーカイブ">
    <meta property="og:description" content="日本の主要な技術系メディアの最新人気エントリーを毎日お届けします。">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{DEFAULT_SITE_CONFIG.site_url}">
    <meta property="og:image" content="{DEFAULT_SITE_CONFIG.og_image_url}">
    <meta property="og:site_name" content="今日のテックニュース">
    
    <!-- Twitter Card Tags -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:creator" content="@unsoluble_sugar">
    <meta name="twitter:title" content="テックニュース アーカイブ">
    <meta name="twitter:description" content="日本の主要な技術系メディアの最新人気エントリーを毎日お届けします。">
    <meta name="twitter:image" content="{DEFAULT_SITE_CONFIG.og_image_url}">
    
    <!-- Favicon Links -->
    <link rel="apple-touch-icon" sizes="180x180" href="../assets/favicons/apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="32x32" href="../assets/favicons/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="../assets/favicons/favicon-16x16.png">
    <link rel="manifest" href="../assets/favicons/site.webmanifest">
    <link rel="shortcut icon" href="../assets/favicons/favicon.ico">
    
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }
        h1 {
            color: #1f2328;
        }
        ul {
            list-style-type: disc;
            padding-left: 2em;
        }
        li {
            margin: 8px 0;
        }
        a {
            color: #0969da;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .back-link {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e1e5e9;
        }
    </style>
</head>
<body>
    <h1>テックニュース アーカイブ</h1>
    
    <p>過去のテックニュースの年別アーカイブです。</p>
    
    <ul>"""
    
    for year_dir in reversed(year_dirs):  # 新しい順
        year = year_dir.name
        html_content += f'\n        <li><a href="{year}/index.html">{year}年</a></li>'
    
    html_content += """
    </ul>
    
    <div class="back-link">
        <p><a href="../index.html">← メインページに戻る</a></p>
    </div>
</body>
</html>"""
    
    with open(archives_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

def update_readme_with_archive_link(content):
    """README.mdにアーカイブとRSSへのリンクを追加（既に含まれている場合はそのまま）"""
    # generate_markdown関数で既にアーカイブとRSSリンクが含まれているため、
    # 追加処理は不要。そのまま返す
    return content

def generate_rss_feed(all_entries, date_obj):
    """RSS XMLフィードを生成"""
    # RSS要素の作成
    rss = ET.Element('rss', version='2.0', attrib={'xmlns:atom': 'http://www.w3.org/2005/Atom'})
    channel = ET.SubElement(rss, 'channel')
    
    # チャンネル情報
    ET.SubElement(channel, 'title').text = '今日のテックニュース'
    ET.SubElement(channel, 'link').text = DEFAULT_SITE_CONFIG.site_url
    ET.SubElement(channel, 'description').text = '日本の主要な技術系メディアの最新人気エントリーを毎日お届けします'
    ET.SubElement(channel, 'language').text = 'ja'
    ET.SubElement(channel, 'pubDate').text = date_obj.strftime('%a, %d %b %Y %H:%M:%S +0000')
    ET.SubElement(channel, 'lastBuildDate').text = date_obj.strftime('%a, %d %b %Y %H:%M:%S +0000')
    
    # Atom自己参照リンク
    atom_link = ET.SubElement(channel, 'atom:link')
    atom_link.set('href', DEFAULT_SITE_CONFIG.rss_url)
    atom_link.set('rel', 'self')
    atom_link.set('type', 'application/rss+xml')
    
    # 各フィードからアイテムを追加
    for feed_name, entries in all_entries.items():
        # エントリーはすでにURL重複除去済み
        for entry in entries:
            item = ET.SubElement(channel, 'item')
            # RSSタイトルはプレーンテキストのみ（HTMLタグや絵文字を除去）
            clean_title = re.sub(r'<[^>]+>', '', entry.title)  # HTMLタグを除去
            ET.SubElement(item, 'title').text = clean_title
            ET.SubElement(item, 'link').text = entry.link
            ET.SubElement(item, 'description').text = f'{feed_name}からの記事: {entry.title}'
            ET.SubElement(item, 'guid').text = entry.link
            
            # 公開日（エントリーに日付があれば使用、なければ今日）
            pub_date = getattr(entry, 'published_parsed', None)
            if pub_date:
                pub_datetime = datetime.datetime(*pub_date[:6])
                ET.SubElement(item, 'pubDate').text = pub_datetime.strftime('%a, %d %b %Y %H:%M:%S +0000')
            else:
                ET.SubElement(item, 'pubDate').text = date_obj.strftime('%a, %d %b %Y %H:%M:%S +0000')
    
    return rss

def save_rss_feed(rss_element):
    """RSS XMLファイルを保存"""
    # XMLを整形して保存
    rough_string = ET.tostring(rss_element, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ", encoding='utf-8')
    
    with open("rss.xml", "wb") as f:
        f.write(pretty_xml)
    
    print("RSS feed generated: rss.xml")

def generate_slack_message(all_entries, date):
    """Slack通知用のメッセージを生成"""
    # 注目記事をピックアップ（各フィードから1-2件）
    featured_articles = []
    
    # 優先度の高いフィードから記事を選択
    priority_feeds = ["Tech Blog Weekly", "Zenn", "Qiita", "はてなブックマーク - IT（人気）"]
    
    for feed_name in priority_feeds:
        if feed_name in all_entries and all_entries[feed_name]:
            # 各フィードから最大2件取得
            for entry in all_entries[feed_name][:2]:
                if len(featured_articles) < 6:  # 最大6件まで
                    # タイトルからHTMLタグを除去
                    clean_title = re.sub(r'<[^>]+>', '', entry.title)
                    featured_articles.append({
                        "title": clean_title,
                        "link": entry.link
                    })
    
    # 総記事数を計算
    total_articles = sum(len(entries) for entries in all_entries.values())
    
    # Slackメッセージのペイロードを生成
    featured_text = "\n".join([
        f"• <{article['link']}|{article['title']}>"
        for article in featured_articles
    ])
    
    slack_payload = {
        "text": f"📰 今日のテックニュース ({date.isoformat()})",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📰 今日のテックニュース ({date.isoformat()})"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🔥 *注目記事*\n{featured_text}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"📊 *更新サマリー*: {total_articles}記事を更新\n\n🔗 <{DEFAULT_SITE_CONFIG.site_url}|カード表示版を見る>\n📰 <{DEFAULT_SITE_CONFIG.github_repo_url}|GitHub リポジトリ>"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "⚡ GitHub Actions で自動更新 | 🚀 キャッシュ機能で高速化"
                    }
                ]
            }
        ]
    }
    
    return slack_payload

def save_slack_message(slack_payload):
    """Slackメッセージをファイルに保存"""
    with open("slack_message.json", "w", encoding="utf-8") as f:
        json.dump(slack_payload, f, ensure_ascii=False, indent=2)
    print("Slack message generated: slack_message.json")

if __name__ == "__main__":
    script_start_time = time.time()
    # JST（日本時間）基準で日付を取得
    jst = datetime.timezone(datetime.timedelta(hours=9))
    today = datetime.datetime.now(jst).date()
    
    all_entries = {}
    for name, feed_url in FEEDS.items():
        print(f"Fetching entries from {name}...")
        entries = fetch_feed_entries(feed_url)
        
        for domain, label in EXCLUDED_DOMAINS.items():
            if domain == 'anond.hatelabo.jp' and name not in ["はてなブックマーク - IT（人気）", "はてなブックマーク - IT（新着）"]:
                continue
            entries = filter_entries_by_domain(entries, domain, label)
        
        all_entries[name] = entries
    
    # ハイライト選定用にフィード間の言及数を数える（重複除去より先に行う）
    mention_counts = count_cross_feed_mentions(all_entries)

    # フィード間URL重複除去と補填
    print("Removing duplicate URLs across feeds...")
    all_entries = deduplicate_urls_across_feeds(all_entries)

    # Markdownコンテンツ生成
    markdown_content = generate_markdown(all_entries, today.isoformat())

    # HTMLコンテンツ生成
    html_content = generate_html(all_entries, today, mention_counts)

    # アーカイブに保存
    archive_file = save_to_archive(all_entries, today, mention_counts)
    print(f"Archived to: {archive_file}")
    
    # インデックスページ更新
    update_monthly_index(today.year, today.month)
    update_yearly_index(today.year)
    update_archive_index()
    
    # daily_news.md更新（アーカイブリンク付き）
    daily_news_content = update_readme_with_archive_link(markdown_content)
    with open("daily_news.md", "w", encoding="utf-8") as f:
        f.write(daily_news_content)
    
    # index.html生成
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("Generated index.html")
    
    # RSSフィード生成
    rss_feed = generate_rss_feed(all_entries, today)
    save_rss_feed(rss_feed)
    
    # Slackメッセージ生成
    slack_message = generate_slack_message(all_entries, today)
    save_slack_message(slack_message)
        
    total_time = time.time() - script_start_time
    print(f"Successfully updated daily_news.md, index.html, archive structure, and RSS feed.")
    print(f"Total execution time: {total_time:.2f} seconds")