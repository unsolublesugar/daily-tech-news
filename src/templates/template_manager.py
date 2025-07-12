"""
テンプレート管理とコンテンツ生成のユーティリティモジュール
"""
from typing import Dict, List, Any, Optional
from config import SiteConfig, PathConfig


class TemplateManager:
    """テンプレート処理を統合管理するクラス"""
    
    def __init__(self, site_config: SiteConfig = None, path_config: PathConfig = None):
        from config.archive_config import DEFAULT_SITE_CONFIG, DEFAULT_PATH_CONFIG
        self.site_config = site_config or DEFAULT_SITE_CONFIG
        self.path_config = path_config or DEFAULT_PATH_CONFIG
    
    def render_favicon(self, favicon: str, feed_name: str) -> str:
        """ファビコンを適切な形式でレンダリング"""
        if favicon.startswith("http"):
            return f'<img src="{favicon}" width="16" height="16" alt="{feed_name}">'
        return favicon
    
    def get_html_head(self, title: str, date_str: str, is_archive: bool = False) -> str:
        """HTML headセクションを生成"""
        og_image_url = self.site_config.og_image_url
        site_description = self.site_config.SITE_DESCRIPTION
        site_url = self.site_config.SITE_URL
        twitter_user = self.site_config.TWITTER_USER
        
        # アーカイブページの場合はURLを調整
        canonical_url = site_url
        if is_archive:
            canonical_url = f"{site_url}archives/{date_str.replace('-', '/')}/{date_str}.html"
        
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
        css_path = "../../assets/css/main.css" if is_archive else "assets/css/main.css"
        return f'    <link rel="stylesheet" href="{css_path}">\n</head>'
    
    def get_navigation_section(self, date_str: str, is_archive: bool = False) -> str:
        """ナビゲーションセクションを生成"""
        site_url = self.site_config.SITE_URL
        hashtags = self.site_config.X_HASHTAGS
        
        # XロゴのインラインSVG
        x_logo_svg = '''<span class="x-logo"><svg viewBox="0 0 1200 1227" xmlns="http://www.w3.org/2000/svg"><path d="M714.163 519.284L1160.89 0H1055.03L667.137 450.887L357.328 0H0L468.492 681.821L0 1226.37H105.866L515.491 750.218L842.672 1226.37H1200L714.137 519.284H714.163ZM569.165 687.828L521.697 619.934L144.011 79.6944H306.615L611.412 515.685L658.88 583.579L1055.08 1150.3H892.476L569.165 687.854V687.828Z" fill="white"/></svg></span>'''
        
        if is_archive:
            # アーカイブページ用のナビゲーション
            tweet_url = f"https://twitter.com/intent/tweet?text=👨‍💻 今日のテックニュース ({date_str}) をチェック！&url={site_url}archives/{date_str.replace('-', '/')}/{date_str}.html&hashtags={hashtags}"
            return f'''<p><a href="{tweet_url}" target="_blank" rel="noopener" class="share-button">{x_logo_svg}シェア</a> | 📚 <a href="../index.html">アーカイブ一覧</a></p>'''
        else:
            # メインページ用のナビゲーション
            tweet_url = f"https://twitter.com/intent/tweet?text=👨‍💻 今日のテックニュース ({date_str}) をチェック！&url={site_url}&hashtags={hashtags}"
            return f'''<p><a href="{tweet_url}" target="_blank" rel="noopener" class="share-button">{x_logo_svg}シェア</a> | 📚 <a href="archives/index.html">過去のニュースを見る</a></p>'''
    
    def get_footer_section(self, is_archive: bool = False) -> str:
        """フッターセクションを生成"""
        site_url = self.site_config.SITE_URL
        twitter_user = self.site_config.TWITTER_USER
        
        main_page_link = ""
        rss_link = ""
        
        if is_archive:
            main_page_link = '<p><a href="../../index.html" class="nav-button">🏠 メインページに戻る</a></p>\n        '
            rss_link = f'<p>📡 <a href="{site_url}rss.xml">RSSフィードを購読</a></p>\n        '
        
        return f'''
    <div class="footer">
        {main_page_link}{rss_link}<p>🚀 運営者: <a href="https://x.com/{twitter_user.lstrip('@')}" target="_blank" rel="noopener">{twitter_user}</a> | 
        📁 <a href="https://github.com/unsolublesugar/daily-tech-news" target="_blank" rel="noopener">GitHub Repository</a></p>
    </div>'''
    
    def render_card(self, entry: Any, feed_name: str, thumbnail_url: str = None) -> str:
        """記事カードをレンダリング"""
        title = entry.title
        link = entry.link
        
        # HTMLエスケープ
        escaped_title = title.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        
        if thumbnail_url:
            escaped_url = thumbnail_url.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
            return f'''    <a href="{link}" class="card">
        <div class="card-content">
            <img src="{escaped_url}" width="120" height="90" alt="{escaped_title}" class="card-image">
            <div class="card-text">
                <h4 class="card-title">{title}</h4>
                <p class="card-source">{feed_name}</p>
            </div>
        </div>
    </a>'''
        else:
            return f'''    <a href="{link}" class="card">
        <div class="card-content">
            <div class="card-text">
                <h4 class="card-title">{title}</h4>
                <p class="card-source">{feed_name}</p>
            </div>
        </div>
    </a>'''
    
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
            x_logo_path = "../../assets/x-logo/logo-white.png" if is_archive else "assets/x-logo/logo-white.png"
        
        head_section = self.template_manager.get_html_head(title, date_str, is_archive)
        css_section = self.template_manager.get_css_link(is_archive)
        navigation = self.template_manager.get_navigation_section(date_str, is_archive)
        footer = self.template_manager.get_footer_section(is_archive)
        
        description = self.template_manager.site_config.SITE_DESCRIPTION
        
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