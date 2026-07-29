"""
アーカイブ生成機能を統合管理するモジュール
"""
import json
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

    def write_static_partials(self) -> None:
        """全ページ共通で読み込む静的パーツ（assets/partials/）を書き出す

        フッター・絞り込みシートは各ページに直接埋め込まず、app.js が
        起動時にこれらのファイルを fetch して差し込む。内容の変更は
        ここを更新するだけで全ページに反映され、生成済みページの
        再生成が不要になる。
        """
        footer_html = self.template_manager.get_static_footer_partial_html()
        self._save_content(footer_html, "assets/partials/footer.html")

        filter_sheet_html = self.template_manager.get_static_filter_sheet_partial_html()
        self._save_content(filter_sheet_html, "assets/partials/filter_sheet.html")

    # ---------------------------------------------------------------
    # 記事タブ
    # ---------------------------------------------------------------

    def _article_feeds(self, all_entries: Dict[str, List[Any]]) -> List[str]:
        """記事タブに出すフィード名を、エントリのあるものだけ元の順序で返す"""
        return [name for name, entries in all_entries.items()
                if is_article_feed(name) and entries]

    def _tally_top_categories(self, titles: List[str], limit: int = 2) -> List[str]:
        """タイトル群からカテゴリを判定し、出現数の多い順に返す（フォールバック分類は除く）"""
        tm = self.template_manager
        counts: Dict[str, int] = {}
        for title in titles:
            for category in tm.categorize_article(title):
                if category == tm.FALLBACK_CATEGORY:
                    continue
                counts[category] = counts.get(category, 0) + 1

        ranked = sorted(counts.items(), key=lambda item: -item[1])
        return [category for category, _ in ranked[:limit]]

    def build_day_summary(self, all_entries: Dict[str, List[Any]], date_obj: datetime,
                          mention_counts: Dict[str, int] = None,
                          now: datetime = None) -> Dict[str, Any]:
        """アーカイブ索引（archives/index.json）用の日別サマリーを生成"""
        titles = []
        for feed_name in self._article_feeds(all_entries):
            titles.extend(entry.title for entry in all_entries[feed_name])

        highlights = self.select_highlights(all_entries, mention_counts, limit=1, now=now)
        headline = highlights[0]['title'] if highlights else (titles[0] if titles else '')

        return {
            'date': date_obj.strftime('%Y-%m-%d'),
            'count': len(titles),
            'headline': headline,
            'top_categories': self._tally_top_categories(titles),
        }

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
            meta_parts = [get_media_short_name(item['feed_name'])]
            if item['mentions'] > 1:
                meta_parts.append(f"他{item['mentions'] - 1}メディアで言及")
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
                           now: datetime = None,
                           date_obj: datetime = None,
                           is_archive: bool = False) -> str:
        """記事タブ（メディア目次＋ハイライト＋メディアごと3件固定）を生成"""
        tm = self.template_manager
        now = now or datetime.now(JST)
        display_count = self.site_config.DISPLAY_PER_MEDIA

        feed_names = self._article_feeds(all_entries)
        if not feed_names:
            return '            <p class="empty-note">記事を取得できませんでした。</p>\n'

        if is_archive and date_obj is not None:
            highlights_heading = f"{date_obj.month}/{date_obj.day}のハイライト"
        else:
            highlights_heading = "今日のハイライト"

        highlights = self.select_highlights(all_entries, mention_counts, now=now)
        highlight_links = {item['link'] for item in highlights}

        # ハイライトに出した記事はメディアセクションから外す（ファーストビューとの重複回避）。
        # 除外してから display_count 件を取るので、表示件数は減らず次の記事が繰り上がる。
        sections = []
        for feed_name in feed_names:
            entries = [entry for entry in all_entries[feed_name]
                       if entry.link not in highlight_links]
            if entries:
                sections.append((feed_name, entries[:display_count]))

        if not sections:
            return tm.render_highlights(highlights, heading=highlights_heading)

        html_content = tm.render_media_toc([feed_name for feed_name, _ in sections])
        html_content += tm.render_highlights(highlights, heading=highlights_heading)

        for feed_name, entries in sections:
            rows = ''
            for entry in entries:
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
            articles_html=self.build_articles_tab(all_entries, mention_counts, now, date_obj, is_archive),
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
    """アーカイブ索引（年月タブ＋カレンダーの1ページ）の生成を管理するクラス

    日別サマリーを archives/index.json に蓄積し、そこから
    archives/index.html（Web版）と archives/index.md（Markdown版）を組み立てる。
    """

    INDEX_JSON_FILENAME = "index.json"

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

    @property
    def _index_json_path(self) -> Path:
        return Path(self.site_config.ARCHIVE_BASE_DIR) / self.INDEX_JSON_FILENAME

    def load_index(self) -> List[Dict[str, Any]]:
        """archives/index.json を読み込む（存在しなければ空リスト）"""
        path = self._index_json_path
        if not path.exists():
            return []
        with open(path, encoding='utf-8') as f:
            return json.load(f)

    def _save_index(self, day_summaries: List[Dict[str, Any]]) -> None:
        sorted_summaries = sorted(day_summaries, key=lambda d: d['date'])
        self._ensure_directory(str(self._index_json_path.parent))
        with open(self._index_json_path, 'w', encoding='utf-8') as f:
            json.dump(sorted_summaries, f, ensure_ascii=False, indent=2)
            f.write('\n')

    @staticmethod
    def _group_by_month(day_summaries: List[Dict[str, Any]]) -> Dict[Tuple[int, int], List[Dict[str, Any]]]:
        groups: Dict[Tuple[int, int], List[Dict[str, Any]]] = {}
        for day in day_summaries:
            year, month, _ = day['date'].split('-')
            groups.setdefault((int(year), int(month)), []).append(day)
        for days in groups.values():
            days.sort(key=lambda d: d['date'], reverse=True)
        return groups

    def generate_index_html(self, day_summaries: List[Dict[str, Any]]) -> str:
        """archives/index.html（年月タブ＋カレンダーの1ページ）を生成"""
        tm = self.template_manager
        site_url = self.site_config.site_url

        if not day_summaries:
            groups = {}
            months_sorted = []
            latest_date = ''
        else:
            groups = self._group_by_month(day_summaries)
            months_sorted = sorted(groups.keys(), reverse=True)
            latest_date = max(d['date'] for d in day_summaries)

        month_tabs_html = tm.render_month_tabs(months_sorted)
        panels_html = ''.join(
            tm.render_month_panel(year, month, groups[(year, month)], latest_date, is_active=(idx == 0))
            for idx, (year, month) in enumerate(months_sorted)
        )
        if not panels_html:
            panels_html = '        <p class="empty-note">アーカイブがまだありません。</p>\n'

        header_html = tm.get_archive_index_header_html(len(day_summaries), month_tabs_html)
        head_section = tm.get_html_head(
            "アーカイブ | 今日のテックニュース", '', is_archive=True, depth=1,
            canonical_url=f"{site_url}archives/index.html"
        )
        footer_html = tm.get_footer_html()
        js_path = f"{tm.get_asset_prefix(True, 1)}assets/js/app.js"

        return f"""{head_section}
<body>
<div class="app">
{header_html}
    <main class="app-main">
{panels_html}    </main>

{footer_html}
</div>
    <script src="{js_path}"></script>
</body>
</html>"""

    def generate_index_markdown(self, day_summaries: List[Dict[str, Any]]) -> str:
        """archives/index.md（Markdown版の日付一覧）を生成"""
        md_content = "# 📚 過去のニュース一覧\n\n"
        md_content += f"{self.site_config.SITE_DESCRIPTION}\n\n"
        md_content += f"Web版はこちら： {self.site_config.site_url}archives/index.html\n\n"

        if not day_summaries:
            md_content += "アーカイブファイルが見つかりませんでした。\n"
        else:
            groups = self._group_by_month(day_summaries)
            for year, month in sorted(groups.keys(), reverse=True):
                md_content += f"## {year}年{month}月\n\n"
                for day in groups[(year, month)]:
                    date_str = day['date']
                    day_num = date_str.split('-')[2]
                    headline = day.get('headline') or '概要なし'
                    md_content += (
                        f"- [{month:02d}/{day_num}]({year}/{month:02d}/{date_str}.md) "
                        f"| [Web版]({year}/{month:02d}/{date_str}.html) — {headline}\n"
                    )
                md_content += "\n"

        md_content += "[← メインページに戻る](../daily_news.md)\n"

        return md_content

    def update_index(self, day_summary: Dict[str, Any]) -> None:
        """1日分のサマリーを索引に反映し、index.json / index.html / index.md を更新"""
        day_summaries = [d for d in self.load_index() if d['date'] != day_summary['date']]
        day_summaries.append(day_summary)
        self._save_index(day_summaries)

        self._save_content(self.generate_index_html(day_summaries),
                           f"{self.site_config.ARCHIVE_BASE_DIR}/index.html")
        self._save_content(self.generate_index_markdown(day_summaries),
                           f"{self.site_config.ARCHIVE_BASE_DIR}/index.md")

    def update_all_indexes(self) -> None:
        """現在の archives/index.json から index.html / index.md を再生成する"""
        day_summaries = self.load_index()
        self._save_content(self.generate_index_html(day_summaries),
                           f"{self.site_config.ARCHIVE_BASE_DIR}/index.html")
        self._save_content(self.generate_index_markdown(day_summaries),
                           f"{self.site_config.ARCHIVE_BASE_DIR}/index.md")
        print(f"Updated: {self.site_config.ARCHIVE_BASE_DIR}/index.html")
        print(f"Updated: {self.site_config.ARCHIVE_BASE_DIR}/index.md")