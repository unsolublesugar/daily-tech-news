"""
アーカイブ生成機能を統合管理するモジュール
"""
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from config import SiteConfig, PathConfig, DEFAULT_SITE_CONFIG, DEFAULT_PATH_CONFIG
from templates import TemplateManager, ContentStructure


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
    
    def _process_entries(self, all_entries: Dict[str, List[Any]], 
                        feed_info: Dict[str, Dict], thumbnails: Dict[str, str] = None) -> str:
        """エントリを処理してHTML文字列を生成"""
        html_content = ""
        
        for feed_name, entries in all_entries.items():
            favicon = feed_info[feed_name]["favicon"]
            favicon_display = self.template_manager.render_favicon(favicon, feed_name)
            
            html_content += f"    <h2>{favicon_display} {feed_name}</h2>\n"
            
            if not entries:
                html_content += "    <p>記事を取得できませんでした。</p>\n"
            else:
                for entry in entries:
                    thumbnail_url = thumbnails.get(entry.link) if thumbnails else None
                    card_html = self.template_manager.render_card(entry, feed_name, thumbnail_url)
                    html_content += card_html + "\n"
        
        return html_content
    
    def _process_entries_markdown(self, all_entries: Dict[str, List[Any]], 
                                 feed_info: Dict[str, Dict]) -> str:
        """エントリを処理してMarkdown文字列を生成"""
        markdown_content = ""
        
        for feed_name, entries in all_entries.items():
            favicon = feed_info[feed_name]["favicon"]
            favicon_display = self.template_manager.render_favicon(favicon, feed_name)
            
            markdown_content += f"## {favicon_display} {feed_name}\n\n"
            
            if not entries:
                markdown_content += "記事を取得できませんでした。\n"
            else:
                for entry in entries:
                    entry_markdown = self.template_manager.render_markdown_entry(entry)
                    markdown_content += entry_markdown + "\n"
            
            markdown_content += "\n\n---\n"
        
        return markdown_content
    
    def generate_daily_archive(self, all_entries: Dict[str, List[Any]], 
                              feed_info: Dict[str, Dict], date_obj: datetime,
                              thumbnails: Dict[str, str] = None) -> Tuple[str, str]:
        """日次アーカイブ（HTML・Markdown）を生成"""
        date_str = date_obj.strftime('%Y-%m-%d')  # T00:00:00を除去
        title = self.site_config.get_site_title(date_str)
        
        # HTML生成
        entries_html = self._process_entries(all_entries, feed_info, thumbnails)
        html_content = self.content_structure.build_html_page(
            title, date_str, entries_html, is_archive=True
        )
        
        # Markdown生成
        entries_markdown = self._process_entries_markdown(all_entries, feed_info)
        markdown_content = self.content_structure.build_markdown_page(
            title, date_str, entries_markdown, is_archive=True
        )
        
        return html_content, markdown_content
    
    def save_daily_archive(self, all_entries: Dict[str, List[Any]], 
                          feed_info: Dict[str, Dict], date_obj: datetime,
                          thumbnails: Dict[str, str] = None) -> Tuple[str, str]:
        """日次アーカイブを生成してファイルに保存"""
        year = date_obj.year
        month = date_obj.month
        day = date_obj.day
        
        # コンテンツ生成
        html_content, markdown_content = self.generate_daily_archive(
            all_entries, feed_info, date_obj, thumbnails
        )
        
        # ファイルパス生成
        html_path = self.path_config.get_archive_file_path(year, month, day, "html")
        md_path = self.path_config.get_archive_file_path(year, month, day, "md")
        
        # ファイル保存
        self._save_content(html_content, html_path)
        self._save_content(markdown_content, md_path)
        
        print(f"Archive saved: {html_path}, {md_path}")
        return html_path, md_path
    
    def generate_main_page(self, all_entries: Dict[str, List[Any]], 
                          feed_info: Dict[str, Dict], date_str: str,
                          thumbnails: Dict[str, str] = None) -> Tuple[str, str]:
        """メインページ（HTML・Markdown）を生成"""
        title = self.site_config.get_site_title(date_str)
        
        # HTML生成
        entries_html = self._process_entries(all_entries, feed_info, thumbnails)
        
        # メインページ用のRSS情報を追加
        rss_info = '''
    <div class="rss-info">
        <strong>📡 RSS配信について</strong><br>
        このサイトでは RSS フィードを配信しています。お好みのRSSリーダーに登録してご利用ください。<br>
        <a href="rss.xml" target="_blank" rel="noopener">RSS フィード</a>
    </div>
'''
        entries_html += rss_info
        
        html_content = self.content_structure.build_html_page(
            title, date_str, entries_html, is_archive=False
        )
        
        # Markdown生成
        entries_markdown = self._process_entries_markdown(all_entries, feed_info)
        markdown_content = self.content_structure.build_markdown_page(
            title, date_str, entries_markdown, is_archive=False
        )
        
        return html_content, markdown_content
    
    def convert_markdown_to_html(self, markdown_path: str, target_html_path: str = None) -> str:
        """既存のMarkdownファイルをHTMLに変換（簡易版）"""
        if not os.path.exists(markdown_path):
            raise FileNotFoundError(f"Markdown file not found: {markdown_path}")
        
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 簡易的なMarkdown→HTML変換
        lines = content.split('\n')
        html_lines = ['<body>', '<div class="content">']
        
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                # h1タグ
                title = line[2:]
                html_lines.append(f'<h1>{title}</h1>')
            elif line.startswith('## '):
                # h2タグ
                heading = line[3:]
                html_lines.append(f'<h2>{heading}</h2>')
            elif line.startswith('- ['):
                # リンクリスト
                # - [タイトル](URL) の形式を想定
                import re
                match = re.match(r'- \[([^\]]+)\]\(([^)]+)\)', line)
                if match:
                    title, url = match.groups()
                    html_lines.append(f'<p><a href="{url}">{title}</a></p>')
                else:
                    html_lines.append(f'<p>{line}</p>')
            elif line == '---':
                html_lines.append('<hr>')
            elif line:
                html_lines.append(f'<p>{line}</p>')
        
        html_lines.extend(['</div>', '</body>'])
        html_content = '\n'.join(html_lines)
        
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