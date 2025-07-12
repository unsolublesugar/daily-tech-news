"""
アーカイブ生成のための設定管理モジュール
"""
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class SiteConfig:
    """サイト全体の設定を管理するクラス"""
    
    # サイト基本情報
    SITE_TITLE_TEMPLATE: str = "👨‍💻 今日のテックニュース ({date})"
    SITE_DESCRIPTION: str = "日本の主要な技術系メディアの最新人気エントリーを毎日お届けします。"
    SITE_URL: str = "https://unsolublesugar.github.io/daily-tech-news/"
    TWITTER_USER: str = "@unsoluble_sugar"
    
    # フィード設定
    MAX_ENTRIES_DEFAULT: int = 5
    MAX_ENTRIES_EVENTS: int = 10
    PRIORITY_FEEDS: List[str] = None
    
    # アーカイブ設定
    ARCHIVE_BASE_DIR: str = "archives"
    
    # OGP画像設定
    OG_IMAGE_FILENAME: str = "assets/images/OGP.png"
    
    # X(Twitter) 設定
    X_LOGO_PATH: str = "assets/x-logo/logo-white.png"
    X_HASHTAGS: str = "techhunter"
    
    def __post_init__(self):
        if self.PRIORITY_FEEDS is None:
            self.PRIORITY_FEEDS = [
                "Tech Blog Weekly", 
                "Zenn", 
                "Qiita", 
                "はてなブックマーク - IT（人気）"
            ]
    
    @property
    def og_image_url(self) -> str:
        """OGP画像の完全URLを取得"""
        return f"{self.SITE_URL}{self.OG_IMAGE_FILENAME}"
    
    def get_site_title(self, date_str: str) -> str:
        """日付を含むサイトタイトルを生成"""
        return self.SITE_TITLE_TEMPLATE.format(date=date_str)
    
    def get_max_entries(self, feed_name: str) -> int:
        """フィード名に応じた最大エントリー数を取得"""
        if "イベント" in feed_name:
            return self.MAX_ENTRIES_EVENTS
        return self.MAX_ENTRIES_DEFAULT


@dataclass
class PathConfig:
    """パス関連の設定を管理するクラス"""
    
    # 相対パス設定
    MAIN_TO_ARCHIVE: str = "archives"
    ARCHIVE_TO_MAIN: str = "../.."
    ARCHIVE_TO_MONTHLY: str = ".."
    
    @staticmethod
    def get_archive_dir_path(year: int, month: int = None) -> str:
        """アーカイブディレクトリのパスを生成"""
        if month is None:
            return f"archives/{year}"
        return f"archives/{year}/{month:02d}"
    
    @staticmethod
    def get_archive_file_path(year: int, month: int, day: int, file_type: str = "md") -> str:
        """アーカイブファイルのパスを生成"""
        date_str = f"{year}-{month:02d}-{day:02d}"
        return f"archives/{year}/{month:02d}/{date_str}.{file_type}"
    
    @staticmethod
    def get_relative_main_page_path(depth: int) -> str:
        """階層の深さに応じたメインページへの相対パスを生成"""
        if depth == 0:
            return "index.html"
        elif depth == 1:
            return "../index.html"
        elif depth == 2:
            return "../../index.html"
        else:
            return "../" * depth + "index.html"


# デフォルト設定インスタンス
DEFAULT_SITE_CONFIG = SiteConfig()
DEFAULT_PATH_CONFIG = PathConfig()