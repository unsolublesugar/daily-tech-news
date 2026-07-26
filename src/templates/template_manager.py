"""
テンプレート管理とコンテンツ生成のユーティリティモジュール
"""
import html
import os
import re
import hashlib
from calendar import monthrange
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from config import SiteConfig, PathConfig

# 日本標準時（記事の時刻表示・日付グルーピングの基準）
JST = timezone(timedelta(hours=9))

# テンプレート内のプレースホルダ {{key}}
_PLACEHOLDER_PATTERN = re.compile(r'\{\{(\w+)\}\}')

# 曜日の日本語表記（月曜=0）
WEEKDAY_JA = ['月', '火', '水', '木', '金', '土', '日']

# カレンダーの曜日ヘッダー（月曜始まり）
CALENDAR_WEEKDAY_JA = ['月', '火', '水', '木', '金', '土', '日']


class TemplateManager:
    """テンプレート処理を統合管理するクラス"""

    # 記事のカテゴリ判定に使うキーワード辞書
    # 絞り込みシートのカテゴリ一覧もこの辞書のキーから生成する
    CATEGORY_KEYWORDS: Dict[str, List[str]] = {
        'AI・機械学習': ['AI', 'Claude', 'GPT', '機械学習', 'LLM', 'Gemini', '生成AI', 'ChatGPT', 'OpenAI', 'Anthropic', 'neoAI', 'Reasoning Model', '事前学習', 'ファインチューニング', 'Copilot'],
        'Web開発': ['React', 'Vue', 'JavaScript', 'CSS', 'HTML', 'フロントエンド', 'Next.js', 'TypeScript', 'Angular', 'Svelte', 'Node.js', 'npm', 'webpack', 'Vite', 'Nuxt'],
        'クラウド': ['AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'クラウド', 'サーバーレス', 'Lambda', 'EC2', 'S3', 'Athena', 'BigQuery', 'CloudFormation', 'Oracle Cloud', 'DynamoDB', 'Cloudflare'],
        'モバイル': ['Swift', 'iOS', 'Android', 'React Native', 'Flutter', 'アプリ開発', 'Kotlin', 'Xcode', 'Android Studio', 'モバイル', 'Suica'],
        'ゲーム開発': ['Unity', 'Unreal Engine', 'Unreal', 'ゲーム開発', 'ゲーム制作', 'ゲーム', 'MRTK', 'Mixed Reality Toolkit', 'HoloLens', 'ゲームエンジン'],
        'DevOps': ['CI/CD', 'Jenkins', 'GitHub Actions', 'インフラ', 'デプロイ', 'Docker', 'Terraform', 'Ansible', 'Kubernetes', 'GitOps', 'SRE', 'SLO', 'Datadog'],
        'セキュリティ': ['セキュリティ', '脆弱性', 'HTTPS', '認証', '暗号化', 'サイバー', 'セキュア', '攻撃', 'ペネトレーション', 'OAuth'],
        'データベース': ['MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'データベース', 'SQL', 'NoSQL', 'DynamoDB', 'Firebase', 'Supabase', 'Oracle Database'],
        'データ分析': ['データ分析', 'ビッグデータ', '分析', 'Analytics', 'データサイエンス', 'Tableau', 'Power BI', 'データ可視化', 'ETL', 'データ処理', 'QuickSight', 'SPICE'],
        'プログラミング': ['Python', 'Java', 'Go', 'Rust', 'C++', 'C#', 'PHP', 'Ruby', 'Scala', 'Kotlin', 'Elixir', 'Haskell', 'F#', 'Windows', 'WSL', 'Ubuntu', 'Linux'],
        'ツール・IDE': ['VS Code', 'Visual Studio', 'IntelliJ', 'Eclipse', 'Vim', 'Git', 'GitHub', 'GitLab', 'Notion', 'Slack', 'Claude Code', 'Cursor', 'hawk', 'awk'],
        'アルゴリズム・数学': ['正規表現', '抽象構文木', 'アルゴリズム', '数学', '微分', 'イテレーター', '最適化', 'データ構造', '計算量', 'Brzozowski'],
        'ツール紹介': ['Startpage', '検索エンジン', 'プライベート検索', 'ツール紹介', 'サービス紹介', 'レビュー', 'ツール', 'サービス', 'オープンソース', 'WinActor', 'RPA'],
        '技術発表・LT': ['LT', 'スライド', '発表', 'プレゼン', 'HTML', 'スライド作成', '技術発表', 'カンファレンス', '勉強会', 'SpeakerDeck'],
        'トラブルシューティング': ['トラブルシューティング', 'デバッグ', 'エラー', '問題解決', '障害対応', 'バグ修正', 'ログ解析', 'やってはいけない'],
        'コーディング支援': ['AIコーディング', 'コード生成', 'GitHub Copilot', 'AI支援', 'コーディング', '開発効率', 'IDE拡張', 'GenAI Processors'],
        'ネットワーク': ['ネットワーク', 'TCP/IP', 'HTTP', 'DNS', 'CDN', 'ロードバランサー', 'プロキシ', 'VPN'],
        'UI/UX': ['UI', 'UX', 'デザイン', 'ユーザビリティ', 'プロトタイプ', 'Figma', 'デザインシステム', 'アクセシビリティ'],
        'VR・AR・MR': ['VR', 'AR', 'MR', 'Mixed Reality', 'XR', 'OpenXR', '拡張現実', '仮想現実', '複合現実'],
        'キャリア・組織': ['フルリモート', '居場所', 'キャリア', '組織', 'マネジメント', 'チーム', 'エンジニア', '働き方'],
        'ハードウェア・IoT': ['睡眠トラッカー', 'スマートウォッチ', 'IoT', 'ハードウェア', 'Raspberry Pi', 'ブート'],
        'オープンソース': ['オープンソース', 'OSS', 'ライセンス', 'GPL', 'MIT', 'Apache', 'ライセンス違反'],
        'テクノロジートレンド': ['トレンド', '戦略', 'アップル', 'グーグル', 'OpenAI', '業界動向', 'ガートナー', '量子技術'],
        'システム開発': ['オブジェクト指向', 'サンプルプログラム', '設計', 'アーキテクチャ', 'パターン', '開発手法'],
        'OS・システム': ['Windows', 'Linux', 'Ubuntu', 'openSUSE', 'システム', 'OS', 'ディレクトリ', 'スラッシュ', 'バックスラッシュ']
    }

    # 判定に該当しなかった記事に付ける既定タグ
    FALLBACK_CATEGORY = 'その他'

    # 絞り込みシートのグループ分け。ここに挙げていないカテゴリは「専門・その他」に入る
    FILTER_GROUP_PRIMARY = ['AI・機械学習', 'Web開発', 'クラウド', 'プログラミング', 'ツール・IDE']
    FILTER_GROUP_OPERATION = [
        'DevOps', 'セキュリティ', 'データベース', 'データ分析', 'ネットワーク',
        'OS・システム', 'システム開発', 'トラブルシューティング', 'コーディング支援'
    ]

    def __init__(self, site_config: SiteConfig = None, path_config: PathConfig = None):
        from config.archive_config import DEFAULT_SITE_CONFIG, DEFAULT_PATH_CONFIG
        self.site_config = site_config or DEFAULT_SITE_CONFIG
        self.path_config = path_config or DEFAULT_PATH_CONFIG
        self.template_dir = os.path.join(os.path.dirname(__file__), '../../assets/templates')
        self._template_cache: Dict[str, str] = {}

    def load_template(self, template_name: str) -> str:
        """外部テンプレートファイルを読み込み"""
        if template_name in self._template_cache:
            return self._template_cache[template_name]

        template_path = os.path.join(self.template_dir, template_name)
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"テンプレートファイルが見つかりません: {template_path}")

        self._template_cache[template_name] = content
        return content

    def render_template(self, template_content: str, **kwargs) -> str:
        """テンプレートに変数を展開

        1パスで置換するため、展開後の値に含まれる {{...}} が
        別のキーとして再解釈されることはない。
        未指定のプレースホルダはそのまま残す。
        """
        def _replace(match):
            key = match.group(1)
            if key in kwargs:
                return str(kwargs[key])
            return match.group(0)

        return _PLACEHOLDER_PATTERN.sub(_replace, template_content)

    @staticmethod
    def escape(text: Any) -> str:
        """HTMLテキスト・属性値の両方に使えるようエスケープ"""
        if text is None:
            return ''
        return html.escape(str(text), quote=True)

    # ---------------------------------------------------------------
    # 記事メタ情報の抽出
    # ---------------------------------------------------------------

    def get_entry_datetime(self, entry: Any) -> Optional[datetime]:
        """エントリの公開日時を JST の aware datetime として取得"""
        for attr in ('published_parsed', 'updated_parsed'):
            parsed = getattr(entry, attr, None)
            if parsed:
                try:
                    # feedparser の *_parsed は UTC の time.struct_time
                    return datetime(*parsed[:6], tzinfo=timezone.utc).astimezone(JST)
                except (TypeError, ValueError):
                    continue
        return None

    def format_time_label(self, published: Optional[datetime],
                          now: Optional[datetime] = None) -> str:
        """記事行の右端に出す時刻ラベル（5:20 / 昨日 / 2日前）"""
        if published is None:
            return ''

        now = now or datetime.now(JST)
        delta_days = (now.date() - published.date()).days

        if delta_days <= 0:
            return f"{published.hour}:{published.minute:02d}"
        if delta_days == 1:
            return '昨日'
        return f"{delta_days}日前"

    def extract_summary(self, entry: Any, title: str = '') -> str:
        """記事から「読むか判断するための」要約を抽出

        RSS本文の冒頭をそのまま垂れ流さず、
        - HTML／定型の前置きを除去
        - 文の区切りで切る
        - 意味のある長さにならなければ空文字を返す（＝展開しても要約は出さない）
        """
        raw = ''
        for attr in ('summary', 'description'):
            value = getattr(entry, attr, None)
            if value:
                raw = value
                break

        if not raw:
            content = getattr(entry, 'content', None)
            if isinstance(content, list) and content:
                raw = content[0].get('value', '')

        if not raw:
            return ''

        text = re.sub(r'<[^>]+>', ' ', str(raw))
        text = html.unescape(text)
        text = re.sub(r'\s+', ' ', text).strip()

        # connpass / TECH PLAY の定型前置き（開催日時・会場）は本文ではないので落とす
        text = re.sub(r'^開催日時:.*?開催場所:[^ ]*\s*', '', text)
        text = re.sub(r'^日時:\S+\s*\([^)]*\)\s*\S+\s*会場:\S*\s*', '', text)

        # 「続きを読む」等の末尾リンク文言
        text = re.sub(r'(続きを読む|Read more|もっと見る)\s*$', '', text).strip()

        if not text:
            return ''

        # タイトルの丸写しは情報量がないので捨てる
        normalized_title = re.sub(r'\s+', '', title)
        if normalized_title and re.sub(r'\s+', '', text) == normalized_title:
            return ''

        limit = 140
        if len(text) > limit:
            head = text[:limit]
            # 文末で切れる位置があればそこまで、なければ素直に省略記号
            boundary = max(head.rfind(c) for c in '。！？.!?')
            if boundary >= 60:
                text = head[:boundary + 1]
            else:
                text = head.rstrip() + '…'

        # 短すぎるものは要約として役に立たない
        if len(text) < 20:
            return ''

        return text

    def generate_card_id(self, link: str) -> str:
        """記事リンクからユニークなカードIDを生成"""
        return hashlib.md5(link.encode()).hexdigest()[:8]
    
    def categorize_article(self, title: str, description: str = '') -> List[str]:
        """記事タイトルと概要からカテゴリタグを自動判定"""
        detected_tags = []
        text = f"{title} {description}".lower()

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            # 短いキーワード（3文字以下）は単語境界マッチング、長いキーワードは部分マッチング
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if len(keyword_lower) <= 3:
                    # 短いキーワードは単語境界で厳密マッチ
                    if re.search(r'\b' + re.escape(keyword_lower) + r'\b', text):
                        detected_tags.append(category)
                        break
                else:
                    # 長いキーワードは部分マッチで柔軟性を保つ
                    if keyword_lower in text:
                        detected_tags.append(category)
                        break

        return detected_tags if detected_tags else [self.FALLBACK_CATEGORY]

    def get_filter_groups(self) -> List[Tuple[str, List[str]]]:
        """絞り込みシートのカテゴリをグループ分けして返す

        カテゴリ一覧は CATEGORY_KEYWORDS のキーから生成するため、
        辞書にカテゴリを足せば自動的にシートへ反映される。
        """
        all_categories = list(self.CATEGORY_KEYWORDS.keys())

        primary = [c for c in self.FILTER_GROUP_PRIMARY if c in all_categories]
        operation = [c for c in self.FILTER_GROUP_OPERATION if c in all_categories]
        assigned = set(primary) | set(operation)
        others = [c for c in all_categories if c not in assigned]
        others.append(self.FALLBACK_CATEGORY)

        return [
            ('よく使う', primary),
            ('開発・運用', operation),
            ('専門・その他', others),
        ]

    def get_filter_sheet_html(self) -> str:
        """絞り込みボトムシートのHTMLを生成"""
        groups_html = ''
        for label, categories in self.get_filter_groups():
            if not categories:
                continue
            chips = ''.join(
                '<button type="button" class="filter-chip" data-tag="{tag}">{tag}</button>'.format(
                    tag=self.escape(category)
                )
                for category in categories
            )
            groups_html += (
                '                <div class="filter-group">\n'
                '                    <div class="filter-group-label">{label}</div>\n'
                '                    <div class="filter-chips">{chips}</div>\n'
                '                </div>\n'
            ).format(label=self.escape(label), chips=chips)

        template = self.load_template('filter_sheet.html')
        return self.render_template(template, groups=groups_html)

    # ---------------------------------------------------------------
    # ページ骨格
    # ---------------------------------------------------------------

    def get_asset_prefix(self, is_archive: bool = False, depth: int = 3) -> str:
        """assets/ への相対パスの接頭辞を取得"""
        if not is_archive:
            return ''
        return '../' * depth

    def get_html_head(self, title: str, date_str: str, is_archive: bool = False,
                      depth: int = 3, canonical_url: str = None) -> str:
        """HTML headセクションを生成"""
        og_image_url = self.site_config.og_image_url
        site_description = self.site_config.SITE_DESCRIPTION
        site_url = self.site_config.site_url
        twitter_user = self.site_config.twitter_user
        prefix = self.get_asset_prefix(is_archive, depth)

        if canonical_url is None:
            canonical_url = site_url
            if is_archive and re.fullmatch(r'\d{4}-\d{2}-\d{2}', date_str or ''):
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                archive_path = f"{date_obj.year}/{date_obj.month:02d}"
                canonical_url = f"{site_url}archives/{archive_path}/{date_str}.html"

        escaped_title = self.escape(title)

        return f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escaped_title}</title>

    <!-- OGP Tags -->
    <meta property="og:title" content="{escaped_title}">
    <meta property="og:description" content="{site_description}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{canonical_url}">
    <meta property="og:image" content="{og_image_url}">
    <meta property="og:site_name" content="今日のテックニュース">

    <!-- Twitter Card Tags -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:creator" content="{twitter_user}">
    <meta name="twitter:title" content="{escaped_title}">
    <meta name="twitter:description" content="{site_description}">
    <meta name="twitter:image" content="{og_image_url}">

    <!-- Favicon Links -->{self.get_favicon_links(is_archive, depth)}

    <!-- CSS -->
    <link rel="stylesheet" href="{prefix}assets/css/main.css">

    <!-- 初期描画前にテーマを適用してちらつきを防ぐ -->
    <script>
        (function () {{
            try {{
                var saved = localStorage.getItem('tech-news-theme');
                var theme = saved || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
                document.documentElement.setAttribute('data-theme', theme);
            }} catch (e) {{ /* localStorage 不可の環境では何もしない */ }}
        }})();
    </script>
</head>"""

    def get_favicon_links(self, is_archive: bool = False, depth: int = 3) -> str:
        """faviconリンクタグを生成"""
        favicon_path = f"{self.get_asset_prefix(is_archive, depth)}assets/favicons/"
        return f"""
    <link rel="apple-touch-icon" sizes="180x180" href="{favicon_path}apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="32x32" href="{favicon_path}favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="{favicon_path}favicon-16x16.png">
    <link rel="manifest" href="{favicon_path}site.webmanifest">
    <link rel="shortcut icon" href="{favicon_path}favicon.ico">"""

    def get_header_html(self, date_obj: datetime, is_archive: bool = False,
                        depth: int = 3) -> str:
        """固定ヘッダー（サイト名・日付・絞り込み・テーマ切替・タブ）を生成"""

        if is_archive:
            back_link = f"{'../' * (depth - 1)}index.html"
            date_label = self.format_archive_header_date(date_obj)
            brand = (
                f'<a class="icon-btn" href="{back_link}" aria-label="アーカイブ一覧へ戻る" title="アーカイブ一覧へ戻る">←</a>'
                f'<span class="site-name">{date_label}</span>'
            )
        else:
            date_label = self.format_header_date(date_obj)
            brand = (
                f'<span class="site-name">今日のテックニュース</span>'
                f'<span class="site-date">{date_label}</span>'
            )

        filter_button = (
            '\n            <button type="button" id="filter-open" class="pill-btn">'
            '絞り込み<span class="filter-count" id="filter-count" hidden></span></button>'
        )

        template = self.load_template('header.html')
        return self.render_template(template, brand=brand, filter_button=filter_button)

    def format_header_date(self, date_obj: datetime) -> str:
        """ヘッダー用の日付表記（7/26 (日)）"""
        return f"{date_obj.month}/{date_obj.day} ({WEEKDAY_JA[date_obj.weekday()]})"

    def format_archive_header_date(self, date_obj: datetime) -> str:
        """アーカイブ日別ページのヘッダー用の日付表記（2026/7/26 (日)）"""
        return f"{date_obj.year}/{date_obj.month}/{date_obj.day} ({WEEKDAY_JA[date_obj.weekday()]})"

    def get_footer_html(self, is_archive: bool = False, depth: int = 3) -> str:
        """フッター（RSS行・リンクタイル・クレジット）を生成"""
        prefix = self.get_asset_prefix(is_archive, depth)
        archive_link = f"{prefix}archives/index.html" if not is_archive else f"{prefix}archives/index.html"

        template = self.load_template('footer.html')
        return self.render_template(
            template,
            rss_url=self.site_config.rss_url,
            archive_link=archive_link,
            github_url=self.site_config.github_repo_url,
            profile_url=self.site_config.profile_url,
            profile_name=self.escape(self.site_config.profile_display_name)
        )

    # ---------------------------------------------------------------
    # 記事タブ
    # ---------------------------------------------------------------

    def render_article_row(self, entry: Any, feed_name: str,
                           now: Optional[datetime] = None) -> str:
        """記事行をレンダリング

        サムネイル・著者情報・ホバープレビュー用のDOMは持たない。
        絞り込み用のタグと要約は属性／展開部にのみ埋め込む。
        """
        title = entry.title
        link = entry.link

        summary = self.extract_summary(entry, title)
        tags = self.categorize_article(title, summary)
        published = self.get_entry_datetime(entry)

        # 表示するタグは最大2つ。絞り込みには検出した全タグを使う
        tag_chips = ''.join(
            f'<span class="tag-chip">{self.escape(tag)}</span>' for tag in tags[:2]
        )

        summary_html = ''
        if summary:
            summary_html = f'\n                        <p class="article-summary">{self.escape(summary)}</p>'

        template = self.load_template('article_row.html')
        return self.render_template(
            template,
            card_id=self.generate_card_id(link),
            tags_attr=self.escape(','.join(tags)),
            title=self.escape(title),
            title_attr=self.escape(title),
            time_label=self.escape(self.format_time_label(published, now)),
            tag_chips=tag_chips,
            summary_html=summary_html,
            link=self.escape(link)
        )

    def render_media_section(self, feed_name: str, rows_html: str) -> str:
        """メディアセクション（見出し＋記事行）をレンダリング"""
        template = self.load_template('media_section.html')
        return self.render_template(
            template,
            section_id=self.generate_section_id(feed_name),
            feed_name=self.escape(feed_name),
            rows=rows_html
        )

    def generate_section_id(self, feed_name: str) -> str:
        """メディアセクションのアンカーIDを生成"""
        return 'media-' + hashlib.md5(feed_name.encode('utf-8')).hexdigest()[:8]

    def render_media_toc(self, feed_names: List[str]) -> str:
        """メディア目次チップ（横スクロール）をレンダリング"""
        from config.archive_config import get_media_short_name

        if not feed_names:
            return ''

        chips = ''.join(
            '<a class="toc-chip" href="#{section_id}">{label}</a>'.format(
                section_id=self.generate_section_id(name),
                label=self.escape(get_media_short_name(name))
            )
            for name in feed_names
        )
        return (
            '        <nav class="media-toc" aria-label="メディア目次">\n'
            f'            <div class="media-toc-inner">{chips}</div>\n'
            '        </nav>\n'
        )

    def render_highlights(self, highlights: List[Dict[str, Any]],
                          heading: str = "今日のハイライト") -> str:
        """ハイライト（3件）をレンダリング"""
        if not highlights:
            return ''

        cards = ''
        for index, item in enumerate(highlights, start=1):
            cards += (
                '                <a class="highlight-card" href="{link}" target="_blank" rel="noopener">\n'
                '                    <span class="highlight-rank">{rank}</span>\n'
                '                    <span class="highlight-body">\n'
                '                        <span class="highlight-title">{title}</span>\n'
                '                        <span class="highlight-meta">{meta}</span>\n'
                '                    </span>\n'
                '                </a>\n'
            ).format(
                link=self.escape(item['link']),
                rank=index,
                title=self.escape(item['title']),
                meta=self.escape(item['meta'])
            )

        return (
            '        <section class="highlights">\n'
            '            <div class="highlights-head">\n'
            f'                <span class="highlights-title">{self.escape(heading)}</span>\n'
            '                <span class="highlights-note">複数メディアで話題</span>\n'
            '            </div>\n'
            '            <div class="highlight-cards">\n'
            f'{cards}'
            '            </div>\n'
            '        </section>\n'
        )

    # ---------------------------------------------------------------
    # イベントタブ・書籍タブ
    # ---------------------------------------------------------------

    def render_event_groups(self, groups: List[Dict[str, Any]]) -> str:
        """開催日でグルーピングしたイベント一覧をレンダリング"""
        if not groups:
            return '        <p class="empty-note">直近のイベント情報を取得できませんでした。</p>\n'

        html_content = ''
        for group in groups:
            rows = ''
            for event in group['items']:
                rows += (
                    '                <a class="event-row" href="{link}" target="_blank" rel="noopener">\n'
                    '                    <span class="event-time">{time}</span>\n'
                    '                    <span class="event-body">\n'
                    '                        <span class="event-title">{title}</span>\n'
                    '                        <span class="event-meta">{meta}</span>\n'
                    '                    </span>\n'
                    '                </a>\n'
                ).format(
                    link=self.escape(event['link']),
                    time=self.escape(event['time_label']),
                    title=self.escape(event['title']),
                    meta=self.escape(event['meta'])
                )

            html_content += (
                '            <div class="event-group">\n'
                f'                <h2 class="event-day">{self.escape(group["label"])}</h2>\n'
                f'{rows}'
                '            </div>\n'
            )

        return html_content

    def render_books(self, books: List[Dict[str, Any]]) -> str:
        """近刊書籍の一覧をレンダリング"""
        if not books:
            return '        <p class="empty-note">近刊情報を取得できませんでした。</p>\n'

        rows = ''
        for book in books:
            rows += (
                '            <a class="book-row" href="{link}" target="_blank" rel="noopener">\n'
                '                <span class="book-title">{title}</span>\n'
                '                <span class="book-meta">{meta}</span>\n'
                '            </a>\n'
            ).format(
                link=self.escape(book['link']),
                title=self.escape(book['title']),
                meta=self.escape(book['meta'])
            )
        return rows

    def render_markdown_entry(self, entry: Any) -> str:
        """Markdown形式のエントリをレンダリング"""
        title = entry.title
        link = entry.link
        return f"- [{title}]({link})"

    # ---------------------------------------------------------------
    # アーカイブ索引（年月タブ＋カレンダー）
    # ---------------------------------------------------------------

    def get_archive_index_header_html(self, total_days: int, month_tabs_html: str) -> str:
        """アーカイブ索引ページのヘッダー（戻る・総数・年月タブ）を生成"""
        back_link = f"{self.get_asset_prefix(True, 1)}index.html"
        template = self.load_template('archive_header.html')
        return self.render_template(
            template,
            back_link=back_link,
            total_days=total_days,
            month_tabs=month_tabs_html
        )

    def render_month_tabs(self, months: List[Tuple[int, int]]) -> str:
        """年月タブをレンダリング（先頭タブと年が変わったタブのみ年を表示）"""
        buttons = []
        prev_year = None
        for index, (year, month) in enumerate(months):
            month_key = f"{year}-{month:02d}"
            label = f"{year}年{month}月" if year != prev_year else f"{month}月"
            prev_year = year
            active_class = ' is-active' if index == 0 else ''
            buttons.append(
                f'        <button type="button" class="month-tab{active_class}" data-month="{month_key}">{label}</button>'
            )
        return '\n'.join(buttons)

    def render_calendar(self, year: int, month: int, day_by_number: Dict[int, Dict[str, Any]],
                        latest_date: str) -> str:
        """指定した年月のカレンダーグリッドをレンダリング"""
        first_weekday, days_in_month = monthrange(year, month)
        # Python の monthrange は月曜=0 を返すため、月曜始まりのオフセットはそのまま使える
        leading_empty = first_weekday

        weekday_headers = ''.join(f'<span>{label}</span>' for label in CALENDAR_WEEKDAY_JA)

        cells = ['<span class="calendar-day is-empty"></span>' for _ in range(leading_empty)]
        for day in range(1, days_in_month + 1):
            date_str = f"{year}-{month:02d}-{day:02d}"
            day_info = day_by_number.get(day)
            if day_info is None:
                cells.append(f'<span class="calendar-day">{day}</span>')
                continue

            is_latest = ' is-latest' if date_str == latest_date else ''
            href = f"{year}/{month:02d}/{date_str}.html"
            cells.append(f'<a class="calendar-day{is_latest}" href="{href}">{day}</a>')

        return (
            '            <div class="calendar">\n'
            f'                <div class="calendar-weekdays">{weekday_headers}</div>\n'
            f'                <div class="calendar-grid">{"".join(cells)}</div>\n'
            '                <div class="calendar-legend">\n'
            '                    <span><span class="legend-swatch has"></span>記事あり</span>\n'
            '                    <span><span class="legend-swatch latest"></span>最新</span>\n'
            '                </div>\n'
            '            </div>\n'
        )

    def render_archive_day_list(self, year: int, month: int, days: List[Dict[str, Any]]) -> str:
        """指定した年月の日付一覧（見出し・件数・カテゴリ付き）をレンダリング"""
        rows = ''
        for day in days:
            date_str = day['date']
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            day_num = date_obj.day
            weekday_label = WEEKDAY_JA[date_obj.weekday()]

            headline = day.get('headline') or '概要なし'
            categories = day.get('top_categories') or []
            meta = f"{day.get('count', 0)}本"
            if categories:
                meta += f" ・ {' / '.join(categories)} が多め"

            href = f"{year}/{month:02d}/{date_str}.html"
            rows += (
                '                <a class="archive-day" href="{href}">\n'
                '                    <span class="archive-day-date">\n'
                '                        <span class="archive-day-num">{day_num}</span>\n'
                '                        <span class="archive-day-dow">{dow}</span>\n'
                '                    </span>\n'
                '                    <span class="archive-day-body">\n'
                '                        <span class="archive-day-headline">{headline}</span>\n'
                '                        <span class="archive-day-meta">{meta}</span>\n'
                '                    </span>\n'
                '                </a>\n'
            ).format(
                href=href,
                day_num=day_num,
                dow=weekday_label,
                headline=self.escape(headline),
                meta=self.escape(meta)
            )

        return (
            '            <div class="archive-list">\n'
            f'                <div class="archive-list-head">{year}年{month}月の一覧</div>\n'
            f'{rows}'
            '            </div>\n'
        )

    def render_month_panel(self, year: int, month: int, days: List[Dict[str, Any]],
                           latest_date: str, is_active: bool = False) -> str:
        """カレンダーと日付一覧をまとめた月パネルをレンダリング"""
        day_by_number = {int(day['date'].split('-')[2]): day for day in days}
        calendar_html = self.render_calendar(year, month, day_by_number, latest_date)
        list_html = self.render_archive_day_list(year, month, days)
        hidden_attr = '' if is_active else ' hidden'
        month_key = f"{year}-{month:02d}"

        return (
            f'        <div class="month-panel" data-month="{month_key}"{hidden_attr}>\n'
            f'{calendar_html}'
            f'{list_html}'
            '        </div>\n'
        )


class ContentStructure:
    """コンテンツの構造を定義するクラス"""
    
    def __init__(self, template_manager: TemplateManager):
        self.template_manager = template_manager
    
    def build_html_page(self, title: str, date_obj: datetime,
                        articles_html: str, events_html: str, books_html: str,
                        is_archive: bool = False, depth: int = 3,
                        canonical_url: str = None) -> str:
        """記事／イベント／書籍の3タブを持つページを構築"""
        tm = self.template_manager
        date_str = date_obj.strftime('%Y-%m-%d')

        head_section = tm.get_html_head(title, date_str, is_archive, depth, canonical_url)
        header = tm.get_header_html(date_obj, is_archive, depth)
        footer = tm.get_footer_html(is_archive, depth)
        filter_sheet = tm.get_filter_sheet_html()
        js_path = f"{tm.get_asset_prefix(is_archive, depth)}assets/js/app.js"

        return f"""{head_section}
<body>
<div class="app">
{header}
    <main class="app-main">
        <section class="tab-panel is-active" id="panel-articles" role="tabpanel" data-panel="articles">
{articles_html}        </section>

        <section class="tab-panel" id="panel-events" role="tabpanel" data-panel="events" hidden>
            <p class="panel-note">connpass・TECH PLAY の直近イベント。日付順にまとめて、開催が近いものから表示します。</p>
{events_html}        </section>

        <section class="tab-panel" id="panel-books" role="tabpanel" data-panel="books" hidden>
            <p class="panel-note">O'Reilly Japan の近刊。</p>
{books_html}        </section>
    </main>

{footer}
</div>
{filter_sheet}
    <script src="{js_path}"></script>
</body>
</html>"""

    def build_markdown_page(self, title: str, date_str: str, entries_markdown: str, 
                           is_archive: bool = False) -> str:
        """完全なMarkdownページを構築"""
        site_url = self.template_manager.site_config.site_url
        
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