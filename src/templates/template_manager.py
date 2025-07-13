"""
テンプレート管理とコンテンツ生成のユーティリティモジュール
"""
import os
import re
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from config import SiteConfig, PathConfig


class TemplateManager:
    """テンプレート処理を統合管理するクラス"""
    
    def __init__(self, site_config: SiteConfig = None, path_config: PathConfig = None):
        from config.archive_config import DEFAULT_SITE_CONFIG, DEFAULT_PATH_CONFIG
        self.site_config = site_config or DEFAULT_SITE_CONFIG
        self.path_config = path_config or DEFAULT_PATH_CONFIG
        self.template_dir = os.path.join(os.path.dirname(__file__), '../../assets/templates')
    
    def load_template(self, template_name: str) -> str:
        """外部テンプレートファイルを読み込み"""
        template_path = os.path.join(self.template_dir, template_name)
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"テンプレートファイルが見つかりません: {template_path}")
    
    def render_template(self, template_content: str, **kwargs) -> str:
        """テンプレートに変数を展開"""
        for key, value in kwargs.items():
            placeholder = f"{{{{{key}}}}}"
            template_content = template_content.replace(placeholder, str(value))
        return template_content
    
    def is_valid_thumbnail_url(self, thumbnail_url: str) -> bool:
        """サムネイル画像URLの有効性を確認"""
        if not thumbnail_url or not thumbnail_url.strip():
            return False
        
        # 基本的なURL形式チェック
        if not thumbnail_url.startswith(('http://', 'https://')):
            return False
        
        # 画像拡張子のチェック（一般的な画像形式）
        valid_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg')
        url_lower = thumbnail_url.lower()
        
        # URLパラメータを除去してから拡張子をチェック
        clean_url = url_lower.split('?')[0].split('#')[0]
        
        # 拡張子チェックまたは一般的な画像ホスティングサービスのチェック
        has_valid_extension = clean_url.endswith(valid_extensions)
        is_image_service = any(service in url_lower for service in [
            'imgur.com', 'cdn.', 'images.', 'img.', 'photo.',
            'thumbnail', 'thumb', 'preview', 'avatar'
        ])
        
        return has_valid_extension or is_image_service
    
    def render_favicon(self, favicon: str, feed_name: str) -> str:
        """ファビコンを適切な形式でレンダリング"""
        if favicon.startswith("http"):
            return f'<img src="{favicon}" width="16" height="16" alt="{feed_name}">'
        return favicon
    
    def calculate_read_time(self, text: str) -> str:
        """テキストから推定読時間を計算（日本語対応）"""
        if not text:
            return "約1分"
        
        # HTMLタグを除去
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        # 日本語文字数（ひらがな、カタカナ、漢字）
        japanese_chars = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', clean_text))
        # 英語単語数
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', clean_text))
        
        # 日本語：400文字/分、英語：200単語/分で計算
        japanese_minutes = japanese_chars / 400
        english_minutes = english_words / 200
        
        total_minutes = max(1, round(japanese_minutes + english_minutes))
        
        return f"約{total_minutes}分"
    
    def get_relative_date(self, published_date: str) -> str:
        """公開日から相対的な日付文字列を生成"""
        if not published_date:
            return ""
        
        try:
            # 様々な日付フォーマットに対応
            published = None
            date_formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S%z',
                '%Y-%m-%dT%H:%M:%SZ',
                '%a, %d %b %Y %H:%M:%S %Z',
                '%a, %d %b %Y %H:%M:%S %z',
                '%Y-%m-%d'
            ]
            
            for fmt in date_formats:
                try:
                    published = datetime.strptime(published_date.strip(), fmt)
                    break
                except ValueError:
                    continue
            
            if not published:
                return ""
            
            # タイムゾーン未設定の場合は現在のタイムゾーンとして扱う
            if published.tzinfo is None:
                published = published.replace(tzinfo=datetime.now().astimezone().tzinfo)
            
            now = datetime.now(published.tzinfo)
            diff = now - published
            
            if diff.days > 30:
                return f"{diff.days // 30}ヶ月前"
            elif diff.days > 7:
                return f"{diff.days // 7}週間前"
            elif diff.days > 0:
                return f"{diff.days}日前"
            elif diff.seconds > 3600:
                return f"{diff.seconds // 3600}時間前"
            elif diff.seconds > 60:
                return f"{diff.seconds // 60}分前"
            else:
                return "たった今"
                
        except Exception:
            return ""
    
    def extract_description(self, entry: Any) -> str:
        """記事から説明文を抽出"""
        description = ""
        
        # RSS feedの summary や description フィールドから取得
        if hasattr(entry, 'summary'):
            description = entry.summary
        elif hasattr(entry, 'description'):
            description = entry.description
        elif hasattr(entry, 'content'):
            if isinstance(entry.content, list) and entry.content:
                description = entry.content[0].get('value', '')
            else:
                description = str(entry.content)
        
        if description:
            # HTMLタグを除去
            clean_desc = re.sub(r'<[^>]+>', '', description)
            # 改行や余分な空白を正規化
            clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
            # 300文字程度に制限
            if len(clean_desc) > 300:
                clean_desc = clean_desc[:300] + '...'
            return clean_desc
        
        return "記事の詳細を確認してください。"
    
    def generate_card_id(self, link: str) -> str:
        """記事リンクからユニークなカードIDを生成"""
        return hashlib.md5(link.encode()).hexdigest()[:8]
    
    def get_html_head(self, title: str, date_str: str, is_archive: bool = False) -> str:
        """HTML headセクションを生成"""
        og_image_url = self.site_config.og_image_url
        site_description = self.site_config.SITE_DESCRIPTION
        site_url = self.site_config.SITE_URL
        twitter_user = self.site_config.TWITTER_USER
        
        # アーカイブページの場合はURLを調整
        canonical_url = site_url
        if is_archive:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            archive_path = f"{date_obj.year}/{date_obj.month:02d}"
            canonical_url = f"{site_url}archives/{archive_path}/{date_str}.html"
        
        return f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    
    <!-- OGP Tags -->
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{site_description}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{canonical_url}">
    <meta property="og:image" content="{og_image_url}">
    <meta property="og:site_name" content="今日のテックニュース">
    
    <!-- Twitter Card Tags -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:creator" content="{twitter_user}">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{site_description}">
    <meta name="twitter:image" content="{og_image_url}">"""
    
    def get_css_link(self, is_archive: bool = False) -> str:
        """外部CSSファイルへのリンクを取得"""
        css_path = "../../../assets/css/main.css" if is_archive else "assets/css/main.css"
        js_path = "../../../assets/js/preview.js" if is_archive else "assets/js/preview.js"
        return f'    <link rel="stylesheet" href="{css_path}">\n</head>'
    
    def get_navigation_section(self, date_str: str, is_archive: bool = False) -> str:
        """ナビゲーションセクションを生成（外部テンプレート使用）"""
        site_url = self.site_config.SITE_URL
        hashtags = self.site_config.X_HASHTAGS
        
        if is_archive:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            archive_path = f"{date_obj.year}/{date_obj.month:02d}"
            tweet_url = f"https://twitter.com/intent/tweet?text=👨‍💻 今日のテックニュース ({date_str}) をチェック！&url={site_url}archives/{archive_path}/{date_str}.html&hashtags={hashtags}"
            archive_link = "../index.html"
            archive_text = "アーカイブ一覧"
        else:
            tweet_url = f"https://twitter.com/intent/tweet?text=👨‍💻 今日のテックニュース ({date_str}) をチェック！&url={site_url}&hashtags={hashtags}"
            archive_link = "archives/index.html"
            archive_text = "過去のニュースを見る"
        
        template = self.load_template('navigation.html')
        return self.render_template(
            template,
            tweet_url=tweet_url,
            archive_link=archive_link,
            archive_text=archive_text
        )
    
    def get_footer_section(self, is_archive: bool = False) -> str:
        """フッターセクションを生成（外部テンプレート使用）"""
        site_url = self.site_config.SITE_URL
        twitter_user = self.site_config.TWITTER_USER
        
        main_page_link = ""
        rss_link = ""
        
        if is_archive:
            main_page_link = '<p><a href="../../index.html" class="nav-button">🏠 メインページに戻る</a></p>\n        '
            rss_link = f'<p>📡 <a href="{site_url}rss.xml">RSSフィードを購読</a></p>\n        '
        
        template = self.load_template('footer.html')
        return self.render_template(
            template,
            main_page_link=main_page_link,
            rss_link=rss_link,
            twitter_handle=twitter_user.lstrip('@'),
            twitter_user=twitter_user
        )
    
    def render_card(self, entry: Any, feed_name: str, thumbnail_url: str = None) -> str:
        """記事カードをレンダリング（外部テンプレート使用）"""
        title = entry.title
        link = entry.link
        
        # HTMLエスケープ
        escaped_title = title.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        
        # メタ情報の生成
        description = self.extract_description(entry)
        
        # 公開日の取得（複数のフィールドを試行）
        published_date = ""
        if hasattr(entry, 'published'):
            published_date = entry.published
        elif hasattr(entry, 'updated'):
            published_date = entry.updated
        elif hasattr(entry, 'pubDate'):
            published_date = entry.pubDate
        
        relative_date = self.get_relative_date(published_date)
        read_time = self.calculate_read_time(description)
        card_id = self.generate_card_id(link)
        
        thumbnail = ""
        # サムネイル画像の有効性を確認してからHTMLを生成
        if thumbnail_url and self.is_valid_thumbnail_url(thumbnail_url):
            escaped_url = thumbnail_url.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
            # onerror属性を追加してリンク切れ時に要素を非表示にする
            thumbnail = f'<img src="{escaped_url}" width="120" height="90" alt="{escaped_title}" class="card-image" onerror="this.style.display=\'none\'">'
        
        template = self.load_template('card.html')
        return self.render_template(
            template,
            link=link,
            thumbnail=thumbnail,
            title=title,
            feed_name=feed_name,
            description=description,
            published_date=published_date,
            relative_date=relative_date,
            read_time=read_time,
            card_id=card_id
        )
    
    def render_markdown_entry(self, entry: Any) -> str:
        """Markdown形式のエントリをレンダリング"""
        title = entry.title
        link = entry.link
        return f"- [{title}]({link})"


class ContentStructure:
    """コンテンツの構造を定義するクラス"""
    
    def __init__(self, template_manager: TemplateManager):
        self.template_manager = template_manager
    
    def build_html_page(self, title: str, date_str: str, entries_html: str, 
                       is_archive: bool = False, x_logo_path: str = None) -> str:
        """完全なHTMLページを構築"""
        # X logo pathのデフォルト設定
        if x_logo_path is None:
            x_logo_path = "../../../assets/images/x-logo/logo-white.png" if is_archive else "assets/images/x-logo/logo-white.png"
        
        head_section = self.template_manager.get_html_head(title, date_str, is_archive)
        css_section = self.template_manager.get_css_link(is_archive)
        navigation = self.template_manager.get_navigation_section(date_str, is_archive)
        footer = self.template_manager.get_footer_section(is_archive)
        
        description = self.template_manager.site_config.SITE_DESCRIPTION
        
        # JavaScript path
        js_path = "../../../assets/js/preview.js" if is_archive else "assets/js/preview.js"
        
        return f"""{head_section}
{css_section}
<body>
    <div class="page-header">
        <h1>{title}</h1>
        
        {navigation}
        
        <p>{description}</p>
    </div>
    
{entries_html}
{footer}
    <script src="{js_path}"></script>
</body>
</html>"""
    
    def build_markdown_page(self, title: str, date_str: str, entries_markdown: str, 
                           is_archive: bool = False) -> str:
        """完全なMarkdownページを構築"""
        site_url = self.template_manager.site_config.SITE_URL
        
        if is_archive:
            nav_links = f'📚 [過去のニュースを見る](../../index.md) | 🎨 [カード表示版を見る]({site_url}) | 📡 [RSSフィードを購読]({site_url}rss.xml)'
        else:
            nav_links = f'📚 [過去のニュースを見る](archives/index.md) | 🎨 [カード表示版を見る]({site_url}) | 📡 [RSSフィードを購読]({site_url}rss.xml)'
        
        return f"""# {title}

{nav_links}

{self.template_manager.site_config.SITE_DESCRIPTION}

## 🎨 カード表示版もあります

GitHub Pages版では各記事がカード形式で見やすく表示されます：  
{site_url}

---

{entries_markdown}

## License

This project is licensed under the [MIT License](LICENSE).
"""