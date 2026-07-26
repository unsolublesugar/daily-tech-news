"""
アーカイブ生成機能を統合管理するモジュール
"""
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from config import (
    SiteConfig, PathConfig, DEFAULT_SITE_CONFIG, DEFAULT_PATH_CONFIG,
    is_article_feed, is_book_feed, is_event_feed, get_media_short_name
)
from templates import TemplateManager, ContentStructure
from templates.template_manager import JST, WEEKDAY_JA


@dataclass
class ArchiveEntry:
    """アーカイブエントリの情報を格納するデータクラス"""
    title: str
    link: str
    feed_name: str
    thumbnail_url: Optional[str] = None


class ArchiveGenerator:
    """アーカイブ生成を統合管理するクラス"""
    
    def __init__(self, site_config: SiteConfig = None, path_config: PathConfig = None):
        self.site_config = site_config or DEFAULT_SITE_CONFIG
        self.path_config = path_config or DEFAULT_PATH_CONFIG
        self.template_manager = TemplateManager(self.site_config, self.path_config)
        self.content_structure = ContentStructure(self.template_manager)
    
    def _ensure_directory(self, dir_path: str) -> None:
        """ディレクトリが存在しない場合は作成"""
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def _save_content(self, content: str, file_path: str) -> None:
        """コンテンツをファイルに保存"""
        self._ensure_directory(os.path.dirname(file_path))
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    # ---------------------------------------------------------------
    # 記事タブ
    # ---------------------------------------------------------------

    def _article_feeds(self, all_entries: Dict[str, List[Any]]) -> List[str]:
        """記事タブに出すフィード名を、エントリのあるものだけ元の順序で返す"""
        return [name for name, entries in all_entries.items()
                if is_article_feed(name) and entries]

    def select_highlights(self, all_entries: Dict[str, List[Any]],
                          mention_counts: Dict[str, int] = None,
                          limit: int = 3,
                          now: datetime = None) -> List[Dict[str, Any]]:
        """今日のハイライトを選定する

        複数フィードに重複出現した記事を優先し、足りない分は新着上位で埋める。
        重複回数は fetch 側で（フィード間の重複除去を行う前に）数えたものを受け取る。
        """
        mention_counts = mention_counts or {}
        now = now or datetime.now(JST)
        tm = self.template_manager

        candidates = []
        for feed_name in self._article_feeds(all_entries):
            for entry in all_entries[feed_name]:
                published = tm.get_entry_datetime(entry)
                candidates.append({
                    'title': entry.title,
                    'link': entry.link,
                    'feed_name': feed_name,
                    'published': published,
                    'mentions': mention_counts.get(entry.link, 1),
                })

        if not candidates:
            return []

        def sort_key(item):
            # 言及メディア数が多い順 → 新しい順
            timestamp = item['published'].timestamp() if item['published'] else 0
            return (-item['mentions'], -timestamp)

        candidates.sort(key=sort_key)

        highlights = []
        for item in candidates[:limit]:
            if item['mentions'] > 1:
                mention_label = f"他{item['mentions'] - 1}メディアで言及"
            else:
                mention_label = '新着'

            meta_parts = [get_media_short_name(item['feed_name']), mention_label]
            time_label = tm.format_time_label(item['published'], now)
            if time_label:
                meta_parts.append(time_label)

            highlights.append({
                'title': item['title'],
                'link': item['link'],
                'meta': ' ・ '.join(meta_parts),
            })

        return highlights

    def build_articles_tab(self, all_entries: Dict[str, List[Any]],
                           mention_counts: Dict[str, int] = None,
                           now: datetime = None) -> str:
        """記事タブ（メディア目次＋ハイライト＋メディアごと3件固定）を生成"""
        tm = self.template_manager
        now = now or datetime.now(JST)
        display_count = self.site_config.DISPLAY_PER_MEDIA

        feed_names = self._article_feeds(all_entries)
        if not feed_names:
            return '            <p class="empty-note">記事を取得できませんでした。</p>\n'

        html_content = tm.render_media_toc(feed_names)
        html_content += tm.render_highlights(
            self.select_highlights(all_entries, mention_counts, now=now)
        )

        for feed_name in feed_names:
            rows = ''
            for entry in all_entries[feed_name][:display_count]:
                rows += tm.render_article_row(entry, feed_name, now)
            html_content += tm.render_media_section(feed_name, rows)

        return html_content

    # ---------------------------------------------------------------
    # イベントタブ
    # ---------------------------------------------------------------

    @staticmethod
    def _shorten_place(place: str) -> str:
        """開催場所の表記を短くする（郵便番号を落として市区町村まで）"""
        if not place:
            return ''

        place = re.sub(r'〒\s*\d{3}-?\d{4}\s*', '', place).strip()
        if not place:
            return ''

        # 「東京都豊島区」まで（都道府県が入っている住所）
        match = re.search(r'((?:東京都|北海道|(?:京都|大阪)府|\S{2,3}県).*?[市区町村])', place)
        if match:
            return match.group(1)

        # 都道府県のない住所は先頭の市区町村まで
        match = re.match(r'(\S{1,5}?[市区町村])', place)
        if match:
            return match.group(1)

        return place if len(place) <= 20 else place[:20] + '…'

    def parse_event_schedule(self, entry: Any, feed_name: str) -> Dict[str, Any]:
        """イベントエントリから開催日時と場所を取り出す

        TECH PLAY は独自要素（tp_eventstarttime 等）、
        connpass は summary 冒頭の「開催日時: / 開催場所:」から取得する。
        どちらも取れない場合は start=None（＝「日付不明」グループ行き）。
        """
        start = None
        place = ''

        # TECH PLAY: <tp:eventStartTime> 等の独自要素
        start_time = getattr(entry, 'tp_eventstarttime', '') or ''
        event_date = getattr(entry, 'tp_eventdate', '') or ''
        for value, fmt in ((start_time, '%Y-%m-%d %H:%M:%S'), (event_date, '%Y-%m-%d')):
            if value:
                try:
                    start = datetime.strptime(value.strip(), fmt).replace(tzinfo=JST)
                    break
                except ValueError:
                    continue

        place = (getattr(entry, 'tp_eventplace', '') or
                 getattr(entry, 'tp_eventaddress', '') or '')

        # connpass: summary 冒頭の定型文
        if start is None or not place:
            summary = getattr(entry, 'summary', '') or getattr(entry, 'description', '') or ''
            summary = re.sub(r'<[^>]+>', ' ', str(summary))

            if start is None:
                match = re.search(r'開催日時:\s*(\d{4})/(\d{1,2})/(\d{1,2})(?:\s+(\d{1,2}):(\d{2}))?',
                                  summary)
                if match:
                    year, month, day = (int(match.group(i)) for i in (1, 2, 3))
                    hour = int(match.group(4)) if match.group(4) else 0
                    minute = int(match.group(5)) if match.group(5) else 0
                    has_time = match.group(4) is not None
                    try:
                        start = datetime(year, month, day, hour, minute, tzinfo=JST)
                        if not has_time:
                            start = start.replace(hour=0, minute=0)
                    except ValueError:
                        start = None

            if not place:
                match = re.search(r'開催場所:\s*([^\n]*?)(?:\s{2,}|$)', summary)
                if match:
                    place = match.group(1).strip()

        return {'start': start, 'place': self._shorten_place(place)}

    def build_events_tab(self, all_entries: Dict[str, List[Any]],
                         now: datetime = None) -> str:
        """イベントタブ（開催日で日付グルーピング）を生成

        現行のメディア別ベタ置きをやめ、connpass / TECH PLAY を混ぜて
        開催が近い順に日付ごとへまとめる。
        """
        now = now or datetime.now(JST)
        today = now.date()

        dated: Dict[Any, List[Dict[str, Any]]] = {}
        undated: List[Dict[str, Any]] = []

        for feed_name, entries in all_entries.items():
            if not is_event_feed(feed_name):
                continue

            for entry in entries:
                schedule = self.parse_event_schedule(entry, feed_name)
                start = schedule['start']

                meta_parts = [get_media_short_name(feed_name)]
                if schedule['place']:
                    meta_parts.append(schedule['place'])

                item = {
                    'title': entry.title,
                    'link': entry.link,
                    'meta': ' ・ '.join(meta_parts),
                    'time_label': '',
                    'sort_key': start,
                }

                if start is None:
                    undated.append(item)
                    continue

                # すでに終わった日のイベントは出さない
                if start.date() < today:
                    continue

                if start.hour or start.minute:
                    item['time_label'] = f"{start.hour}:{start.minute:02d}"
                dated.setdefault(start.date(), []).append(item)

        groups = []
        for event_date in sorted(dated.keys()):
            items = sorted(dated[event_date],
                           key=lambda item: item['sort_key'] or datetime.max.replace(tzinfo=JST))
            groups.append({
                'label': f"{event_date.month}/{event_date.day} ({WEEKDAY_JA[event_date.weekday()]})",
                'items': items,
            })

        if undated:
            groups.append({'label': '日付不明', 'items': undated})

        return self.template_manager.render_event_groups(groups)

    # ---------------------------------------------------------------
    # 書籍タブ
    # ---------------------------------------------------------------

    def build_books_tab(self, all_entries: Dict[str, List[Any]]) -> str:
        """書籍タブ（O'Reilly Japan 近刊）を生成"""
        tm = self.template_manager
        books = []

        for feed_name, entries in all_entries.items():
            if not is_book_feed(feed_name):
                continue

            for entry in entries:
                published = tm.get_entry_datetime(entry)
                meta = f"{published.month}/{published.day} 発売" if published else ''
                books.append({
                    'title': entry.title,
                    'link': entry.link,
                    'meta': meta,
                    'sort_key': published,
                })

        # 発売日が近いものから
        books.sort(key=lambda book: book['sort_key'] or datetime.max.replace(tzinfo=JST))

        return tm.render_books(books)

    # ---------------------------------------------------------------
    # ページ生成
    # ---------------------------------------------------------------

    def build_page(self, all_entries: Dict[str, List[Any]], date_obj: datetime,
                   mention_counts: Dict[str, int] = None,
                   is_archive: bool = False, depth: int = 3,
                   now: datetime = None) -> str:
        """記事／イベント／書籍の3タブを持つページ全体を生成"""
        now = now or datetime.now(JST)
        date_str = date_obj.strftime('%Y-%m-%d')
        title = f"今日のテックニュース ({date_str})"

        return self.content_structure.build_html_page(
            title=title,
            date_obj=date_obj,
            articles_html=self.build_articles_tab(all_entries, mention_counts, now),
            events_html=self.build_events_tab(all_entries, now),
            books_html=self.build_books_tab(all_entries),
            is_archive=is_archive,
            depth=depth
        )

    def _process_entries_markdown(self, all_entries: Dict[str, List[Any]]) -> str:
        """エントリを処理してMarkdown文字列を生成"""
        markdown_content = ""

        for feed_name, entries in all_entries.items():
            markdown_content += f"## {feed_name}\n\n"

            if not entries:
                markdown_content += "記事を取得できませんでした。\n"
            else:
                for entry in entries:
                    entry_markdown = self.template_manager.render_markdown_entry(entry)
                    markdown_content += entry_markdown + "\n"

            markdown_content += "\n\n---\n"

        return markdown_content

    def convert_markdown_to_html(self, markdown_path: str, target_html_path: str = None) -> str:
        """既存のMarkdownファイルをHTMLに変換（完全版）"""
        if not os.path.exists(markdown_path):
            raise FileNotFoundError(f"Markdown file not found: {markdown_path}")
        
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # パスの深さを計算してfaviconとCSSのパスを決定
        path_parts = markdown_path.replace(self.site_config.ARCHIVE_BASE_DIR, '').strip('/').split('/')
        depth = len([p for p in path_parts if p])  # archives/, year/, month/ の深さ
        
        # 相対パスを計算
        if depth == 1:  # archives/index.html
            favicon_path = "../assets/favicons/"
            css_path = "../assets/css/main.css"
        elif depth == 2:  # archives/YYYY/index.html
            favicon_path = "../../assets/favicons/"
            css_path = "../../assets/css/main.css"
        elif depth == 3:  # archives/YYYY/MM/index.html
            favicon_path = "../../../assets/favicons/"
            css_path = "../../../assets/css/main.css"
        else:
            favicon_path = "assets/favicons/"
            css_path = "assets/css/main.css"
        
        # タイトルを抽出
        title = "テックニュース アーカイブ"
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break
        
        # HTMLヘッドを生成
        og_image_url = self.site_config.og_image_url
        site_description = self.site_config.SITE_DESCRIPTION
        site_url = self.site_config.site_url
        twitter_user = self.site_config.twitter_user
        
        html_head = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    
    <!-- OGP Tags -->
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{site_description}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{site_url}">
    <meta property="og:image" content="{og_image_url}">
    <meta property="og:site_name" content="今日のテックニュース">
    
    <!-- Twitter Card Tags -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:creator" content="{twitter_user}">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{site_description}">
    <meta name="twitter:image" content="{og_image_url}">
    
    <!-- Favicon Links -->
    <link rel="apple-touch-icon" sizes="180x180" href="{favicon_path}apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="32x32" href="{favicon_path}favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="{favicon_path}favicon-16x16.png">
    <link rel="manifest" href="{favicon_path}site.webmanifest">
    <link rel="shortcut icon" href="{favicon_path}favicon.ico">
    
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
</head>"""
        
        # 簡易的なMarkdown→HTML変換
        lines = content.split('\n')
        html_body_lines = ['<body>', '<div class="content">']
        
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                # h1タグ
                title_text = line[2:]
                html_body_lines.append(f'<h1>{title_text}</h1>')
            elif line.startswith('## '):
                # h2タグ
                heading = line[3:]
                html_body_lines.append(f'<h2>{heading}</h2>')
            elif line.startswith('- ['):
                # リンクリスト
                # - [タイトル](URL) の形式を想定
                import re
                match = re.match(r'- \[([^\]]+)\]\(([^)]+)\)', line)
                if match:
                    title_text, url = match.groups()
                    html_body_lines.append(f'<p><a href="{url}">{title_text}</a></p>')
                else:
                    html_body_lines.append(f'<p>{line}</p>')
            elif line == '---':
                html_body_lines.append('<hr>')
            elif line:
                html_body_lines.append(f'<p>{line}</p>')
        
        html_body_lines.extend(['</div>', '</body>', '</html>'])
        
        # ヘッドとボディを組み合わせて完全なHTMLを生成
        html_content = html_head + '\n' + '\n'.join(html_body_lines)
        
        # ファイル保存
        if target_html_path:
            self._save_content(html_content, target_html_path)
            print(f"Converted HTML saved: {target_html_path}")
        
        return html_content


class ArchiveIndexGenerator:
    """アーカイブインデックスページの生成を管理するクラス"""
    
    def __init__(self, site_config: SiteConfig = None, path_config: PathConfig = None):
        self.site_config = site_config or DEFAULT_SITE_CONFIG
        self.path_config = path_config or DEFAULT_PATH_CONFIG
        self.template_manager = TemplateManager(self.site_config, self.path_config)
    
    def _ensure_directory(self, dir_path: str) -> None:
        """ディレクトリが存在しない場合は作成"""
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def _save_content(self, content: str, file_path: str) -> None:
        """コンテンツをファイルに保存"""
        self._ensure_directory(os.path.dirname(file_path))
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _scan_archive_directories(self) -> Dict[int, List[int]]:
        """アーカイブディレクトリをスキャンして年月の一覧を取得"""
        archives_base = Path(self.site_config.ARCHIVE_BASE_DIR)
        year_month_map = {}
        
        if not archives_base.exists():
            return year_month_map
        
        for year_dir in archives_base.iterdir():
            if year_dir.is_dir() and year_dir.name.isdigit():
                year = int(year_dir.name)
                months = []
                
                for month_dir in year_dir.iterdir():
                    if month_dir.is_dir() and month_dir.name.isdigit():
                        months.append(int(month_dir.name))
                
                if months:
                    year_month_map[year] = sorted(months)
        
        return year_month_map
    
    def _scan_monthly_files(self, year: int, month: int) -> List[str]:
        """指定された年月のアーカイブファイル一覧を取得"""
        month_dir = Path(self.path_config.get_archive_dir_path(year, month))
        files = []
        
        if month_dir.exists():
            for file_path in month_dir.glob("*.md"):
                if file_path.stem != "index":  # インデックスファイルは除外
                    files.append(file_path.stem)
        
        return sorted(files)
    
    def generate_archive_index(self) -> str:
        """総合アーカイブインデックスページを生成"""
        year_month_map = self._scan_archive_directories()
        
        # Markdownコンテンツ生成
        md_content = "# 📚 過去のニュース一覧\n\n"
        md_content += f"{self.site_config.SITE_DESCRIPTION}\n\n"
        md_content += "## 年別アーカイブ\n\n"
        
        if not year_month_map:
            md_content += "アーカイブファイルが見つかりませんでした。\n"
        else:
            for year in sorted(year_month_map.keys(), reverse=True):
                md_content += f"- [{year}年]({year}/index.md)\n"
        
        md_content += f"\n[← メインページに戻る](../README.md)\n"
        
        return md_content
    
    def generate_yearly_index(self, year: int) -> str:
        """年別インデックスページを生成"""
        year_month_map = self._scan_archive_directories()
        months = year_month_map.get(year, [])
        
        md_content = f"# 📅 {year}年のニュース一覧\n\n"
        md_content += f"{self.site_config.SITE_DESCRIPTION}\n\n"
        md_content += "## 月別アーカイブ\n\n"
        
        if not months:
            md_content += f"{year}年のアーカイブファイルが見つかりませんでした。\n"
        else:
            for month in sorted(months, reverse=True):
                md_content += f"- [{month:02d}月]({month:02d}/index.md)\n"
        
        md_content += "\n[← アーカイブ一覧に戻る](../index.md)\n"
        
        return md_content
    
    def generate_monthly_index(self, year: int, month: int) -> str:
        """月別インデックスページを生成"""
        files = self._scan_monthly_files(year, month)
        
        md_content = f"# 📅 {year}年{month:02d}月のニュース一覧\n\n"
        md_content += f"{self.site_config.SITE_DESCRIPTION}\n\n"
        md_content += "## 日別アーカイブ\n\n"
        
        if not files:
            md_content += f"{year}年{month:02d}月のアーカイブファイルが見つかりませんでした。\n"
        else:
            for file_date in sorted(files, reverse=True):
                # ファイル名から日付を抽出 (YYYY-MM-DD形式)
                try:
                    date_parts = file_date.split('-')
                    if len(date_parts) == 3:
                        day = int(date_parts[2])
                        md_content += f"- [{month:02d}月{day:02d}日]({file_date}.md) | [カード表示版]({file_date}.html)\n"
                    else:
                        md_content += f"- [{file_date}]({file_date}.md)\n"
                except (ValueError, IndexError):
                    md_content += f"- [{file_date}]({file_date}.md)\n"
        
        md_content += f"\n[← {year}年一覧に戻る](../index.md)\n"
        
        return md_content
    
    def update_all_indexes(self) -> None:
        """すべてのインデックスページを更新"""
        year_month_map = self._scan_archive_directories()
        
        # 総合インデックス更新
        archive_index_content = self.generate_archive_index()
        self._save_content(archive_index_content, f"{self.site_config.ARCHIVE_BASE_DIR}/index.md")
        print(f"Updated: {self.site_config.ARCHIVE_BASE_DIR}/index.md")
        
        # 年別・月別インデックス更新
        for year, months in year_month_map.items():
            # 年別インデックス
            yearly_content = self.generate_yearly_index(year)
            yearly_path = self.path_config.get_archive_dir_path(year) + "/index.md"
            self._save_content(yearly_content, yearly_path)
            print(f"Updated: {yearly_path}")
            
            # 月別インデックス
            for month in months:
                monthly_content = self.generate_monthly_index(year, month)
                monthly_path = self.path_config.get_archive_dir_path(year, month) + "/index.md"
                self._save_content(monthly_content, monthly_path)
                print(f"Updated: {monthly_path}")