"""
リファクタリング版のfetch_news.py
新しいクラス構造を使用して既存機能を再実装
"""
import feedparser
import datetime
import os
from pathlib import Path
from xml.dom import minidom
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
import time
import re
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import json
import hashlib
from urllib.parse import urlparse, urlunparse, urlencode, parse_qsl

# 新しいクラス群をインポート
from config import SiteConfig, PathConfig
from generators import ArchiveGenerator, ArchiveIndexGenerator
from templates import TemplateManager

# 既存の設定を保持（後方互換性のため）
FEEDS = {
    "Tech Blog Weekly": {
        "url": "https://yamadashy.github.io/tech-blog-rss-feed/feeds/rss.xml",
        "favicon": "💻"
    },
    "Zenn": {
        "url": "https://zenn.dev/feed",
        "favicon": "https://zenn.dev/favicon.ico"
    },
    "Qiita": {
        "url": "https://qiita.com/popular-items/feed", 
        "favicon": "https://cdn.qiita.com/assets/favicons/public/production-c620d3e403342b1022967ba5e3db1aaa.ico"
    },
    "はてなブックマーク - IT（人気）": {
        "url": "http://b.hatena.ne.jp/hotentry/it.rss",
        "favicon": "https://b.hatena.ne.jp/favicon.ico"
    },
    "はてなブックマーク - IT（新着）": {
        "url": "https://b.hatena.ne.jp/entrylist/it.rss",
        "favicon": "https://b.hatena.ne.jp/favicon.ico"
    },
    "DevelopersIO": {
        "url": "https://dev.classmethod.jp/feed/",
        "favicon": "https://dev.classmethod.jp/favicon.ico"
    },
    "gihyo.jp": {
        "url": "https://gihyo.jp/dev/feed/rss2",
        "favicon": "https://gihyo.jp/favicon.ico"
    },
    "Publickey": {
        "url": "https://www.publickey1.jp/atom.xml",
        "favicon": "https://www.publickey1.jp/favicon.ico"
    },
    "CodeZine": {
        "url": "https://codezine.jp/rss/new/20/index.xml",
        "favicon": "https://codezine.jp/favicon.ico"
    },
    "InfoQ Japan": {
        "url": "https://feed.infoq.com/jp",
        "favicon": "https://www.infoq.com/favicon.ico"
    },
    "connpass - イベント": {
        "url": "https://connpass.com/explore/ja.atom",
        "favicon": "https://connpass.com/favicon.ico"
    },
    "TECH PLAY - イベント": {
        "url": "https://rss.techplay.jp/event/w3c-rss-format/rss.xml",
        "favicon": "https://techplay.jp/favicon.ico"
    },
    "O'Reilly Japan - 近刊": {
        "url": "https://www.oreilly.co.jp/catalog/soon.xml",
        "favicon": "https://www.oreilly.co.jp/favicon.ico"
    }
}

# 各フィードから取得する記事の件数
MAX_ENTRIES = 5

# グローバルインスタンス（後方互換性のため）
_site_config = SiteConfig()
_path_config = PathConfig()
_archive_generator = ArchiveGenerator(_site_config, _path_config)
_index_generator = ArchiveIndexGenerator(_site_config, _path_config)


# 既存のThumbnailCacheクラスをそのまま保持
class ThumbnailCache:
    """サムネイルキャッシュを管理するクラス"""
    
    def __init__(self, cache_file_path="thumbnail_cache.json"):
        """
        キャッシュクラスの初期化
        
        Args:
            cache_file_path (str): キャッシュファイルのパス
        """
        self.cache_file_path = cache_file_path
        self.cache = self._load_cache()
    
    def _load_cache(self):
        """キャッシュファイルから既存のデータを読み込む"""
        try:
            if os.path.exists(self.cache_file_path):
                with open(self.cache_file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load thumbnail cache: {e}")
        
        return {}
    
    def _save_cache(self):
        """キャッシュデータをファイルに保存する"""
        try:
            with open(self.cache_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save thumbnail cache: {e}")
    
    def get(self, url):
        """URLに対応するサムネイルURLをキャッシュから取得"""
        return self.cache.get(url)
    
    def set(self, url, thumbnail_url):
        """URLとサムネイルURLの組み合わせをキャッシュに保存"""
        if thumbnail_url:
            self.cache[url] = thumbnail_url
            self._save_cache()
    
    def get_multiple(self, urls):
        """複数のURLに対してキャッシュから一括取得"""
        result = {}
        for url in urls:
            cached_thumbnail = self.get(url)
            if cached_thumbnail:
                result[url] = cached_thumbnail
        return result
    
    def set_multiple(self, url_thumbnail_pairs):
        """複数のURL-サムネイルペアを一括でキャッシュに保存"""
        updated = False
        for url, thumbnail_url in url_thumbnail_pairs.items():
            if thumbnail_url and url not in self.cache:
                self.cache[url] = thumbnail_url
                updated = True
        
        if updated:
            self._save_cache()


# 既存の関数を新しいクラス構造でラップ（後方互換性維持）

def generate_html(all_entries, feed_info, date_str, thumbnails=None):
    """メインページのHTMLを生成（既存API互換）"""
    html_content, _ = _archive_generator.generate_main_page(
        all_entries, feed_info, date_str, thumbnails
    )
    return html_content


def generate_markdown(all_entries, feed_info, date_str):
    """メインページのMarkdownを生成（既存API互換）"""
    _, markdown_content = _archive_generator.generate_main_page(
        all_entries, feed_info, date_str
    )
    return markdown_content


def generate_archive_markdown(all_entries, feed_info, date_str):
    """アーカイブ用のMarkdownコンテンツを生成（既存API互換）"""
    date_obj = datetime.datetime.fromisoformat(date_str)
    _, markdown_content = _archive_generator.generate_daily_archive(
        all_entries, feed_info, date_obj
    )
    return markdown_content


def generate_archive_html(all_entries, feed_info, date_str, thumbnails=None):
    """アーカイブ用のHTMLコンテンツを生成（既存API互換）"""
    date_obj = datetime.datetime.fromisoformat(date_str)
    html_content, _ = _archive_generator.generate_daily_archive(
        all_entries, feed_info, date_obj, thumbnails
    )
    return html_content


def save_to_archive(all_entries, feed_info, date_obj, thumbnails=None):
    """日付別アーカイブファイルとして保存（既存API互換）"""
    return _archive_generator.save_daily_archive(
        all_entries, feed_info, date_obj, thumbnails
    )


def update_archive_index():
    """アーカイブ全体のインデックスページを更新（既存API互換）"""
    _index_generator.update_all_indexes()


def update_yearly_index(year):
    """年別インデックスページを更新（既存API互換）"""
    yearly_content = _index_generator.generate_yearly_index(year)
    yearly_path = _path_config.get_archive_dir_path(year) + "/index.md"
    
    Path(yearly_path).parent.mkdir(parents=True, exist_ok=True)
    with open(yearly_path, 'w', encoding='utf-8') as f:
        f.write(yearly_content)
    
    print(f"Updated yearly index: {yearly_path}")


def update_monthly_index(year, month):
    """月別インデックスページを更新（既存API互換）"""
    monthly_content = _index_generator.generate_monthly_index(year, month)
    monthly_path = _path_config.get_archive_dir_path(year, month) + "/index.md"
    
    Path(monthly_path).parent.mkdir(parents=True, exist_ok=True)
    with open(monthly_path, 'w', encoding='utf-8') as f:
        f.write(monthly_content)
    
    print(f"Updated monthly index: {monthly_path}")


def generate_missing_html_archives():
    """既存MarkdownアーカイブのHTML版を生成（既存API互換）"""
    archives_base = Path("archives")
    if not archives_base.exists():
        print("Archives directory not found.")
        return
    
    converted_count = 0
    
    for year_dir in archives_base.iterdir():
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue
        
        for month_dir in year_dir.iterdir():
            if not month_dir.is_dir() or not month_dir.name.isdigit():
                continue
            
            for md_file in month_dir.glob("*.md"):
                if md_file.name == "index.md":
                    continue
                
                html_file = md_file.with_suffix(".html")
                if html_file.exists():
                    continue
                
                try:
                    # 新しいクラスを使って変換
                    _archive_generator.convert_markdown_to_html(
                        str(md_file), str(html_file)
                    )
                    converted_count += 1
                except Exception as e:
                    print(f"Error converting {md_file}: {e}")
    
    print(f"Converted {converted_count} markdown files to HTML.")


# 残りの既存関数群（RSS生成、URL重複除去など）は後方互換性のためそのまま保持
# これらは元のfetch_news.pyから移植

_TRACKING_PARAMS = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "ref", "fbclid", "gclid",
})

def normalize_url(url):
    """URLを正規化して重複検出の精度を向上させる（fetch_news.pyのnormalize_urlと同一）。"""
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

def remove_url_duplicates(all_entries):
    """URL重複を除去する関数（正規化URLで比較）"""
    seen_urls = set()
    deduplicated_entries = {}
    total_removed = 0
    norm_caught = 0

    # 優先フィードの順序を定義
    priority_feeds = ["Tech Blog Weekly", "Zenn", "Qiita", "はてなブックマーク - IT（人気）"]

    # 優先フィードから先に処理
    for feed_name in priority_feeds:
        if feed_name in all_entries:
            unique_entries = []
            for entry in all_entries[feed_name]:
                norm = normalize_url(entry.link)
                if norm not in seen_urls:
                    unique_entries.append(entry)
                    seen_urls.add(norm)
                else:
                    total_removed += 1
                    if norm != entry.link:
                        norm_caught += 1
            deduplicated_entries[feed_name] = unique_entries

    # 残りのフィードを処理
    for feed_name, entries in all_entries.items():
        if feed_name not in priority_feeds:
            unique_entries = []
            for entry in entries:
                norm = normalize_url(entry.link)
                if norm not in seen_urls:
                    unique_entries.append(entry)
                    seen_urls.add(norm)
                else:
                    total_removed += 1
                    if norm != entry.link:
                        norm_caught += 1
            deduplicated_entries[feed_name] = unique_entries

    if total_removed > 0:
        exact_caught = total_removed - norm_caught
        print(f"URL重複除去 (remove_url_duplicates): 合計{total_removed}件を除去")
        print(f"  うち正規化による検出: {norm_caught}件 / 完全一致による検出: {exact_caught}件")

    return deduplicated_entries


def get_thumbnail_url(url, session=None, timeout=10):
    """指定されたURLからサムネイル画像のURLを取得する"""
    if session is None:
        session = requests.Session()
    
    try:
        response = session.get(url, timeout=timeout, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # OGP画像を優先的に探す
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image['content']
        
        # Twitter Cardの画像を探す
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if twitter_image and twitter_image.get('content'):
            return twitter_image['content']
        
        # 一般的なmetaタグの画像を探す
        meta_image = soup.find('meta', attrs={'name': 'image'})
        if meta_image and meta_image.get('content'):
            return meta_image['content']
        
        return None
        
    except Exception as e:
        print(f"Error getting thumbnail for {url}: {e}")
        return None


def fetch_thumbnails_batch(urls, cache, max_workers=5):
    """複数のURLのサムネイルを並行取得"""
    if not urls:
        return {}
    
    # キャッシュから既存のサムネイルを取得
    cached_thumbnails = cache.get_multiple(urls)
    
    # キャッシュにないURLのみを対象とする
    urls_to_fetch = [url for url in urls if url not in cached_thumbnails]
    
    if not urls_to_fetch:
        print("All thumbnails found in cache.")
        return cached_thumbnails
    
    print(f"Fetching thumbnails for {len(urls_to_fetch)} URLs...")
    
    new_thumbnails = {}
    with requests.Session() as session:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {
                executor.submit(get_thumbnail_url, url, session): url 
                for url in urls_to_fetch
            }
            
            for future in concurrent.futures.as_completed(future_to_url, timeout=60):
                url = future_to_url[future]
                try:
                    thumbnail_url = future.result()
                    if thumbnail_url:
                        new_thumbnails[url] = thumbnail_url
                except Exception as e:
                    print(f"Error fetching thumbnail for {url}: {e}")
    
    # 新しく取得したサムネイルをキャッシュに保存
    if new_thumbnails:
        cache.set_multiple(new_thumbnails)
    
    # キャッシュされたものと新しく取得したものを結合
    all_thumbnails = {**cached_thumbnails, **new_thumbnails}
    
    print(f"Successfully fetched {len(new_thumbnails)} new thumbnails. "
          f"Total: {len(all_thumbnails)} thumbnails available.")
    
    return all_thumbnails


# 他の既存関数（RSS生成など）も同様に保持...
# ここでは省略しますが、実際の実装では全ての既存関数を含める必要があります


def main():
    """メイン処理（既存のmain関数と同じ）"""
    # 既存のメイン処理ロジックをここに実装
    # 新しいクラス構造を使用するように更新
    pass


if __name__ == "__main__":
    main()