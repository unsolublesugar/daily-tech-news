"""
設定管理モジュール

サイト設定、パス設定、環境設定を統一管理
"""

from config.archive_config import (
    SiteConfig,
    PathConfig,
    DEFAULT_SITE_CONFIG,
    DEFAULT_PATH_CONFIG,
    MEDIA_SHORT_NAMES,
    is_article_feed,
    is_book_feed,
    is_event_feed,
    get_media_short_name,
)

__all__ = [
    'SiteConfig',
    'PathConfig',
    'DEFAULT_SITE_CONFIG',
    'DEFAULT_PATH_CONFIG',
    'MEDIA_SHORT_NAMES',
    'is_article_feed',
    'is_book_feed',
    'is_event_feed',
    'get_media_short_name'
]