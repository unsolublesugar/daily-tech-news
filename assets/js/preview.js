/**
 * 記事プレビュー機能
 * デスクトップ：ホバー時にプレビュー表示
 * モバイル：タップ時にプレビュー表示
 */

class ArticlePreview {
    constructor() {
        this.activePreview = null;
        this.isMobile = window.innerWidth <= 768;
        this.previewTimeout = null;
        this.overlay = null;
        
        this.init();
    }
    
    init() {
        this.createOverlay();
        this.attachEventListeners();
        this.handleResize();
    }
    
    createOverlay() {
        // モバイル用のオーバーレイ背景を作成
        this.overlay = document.createElement('div');
        this.overlay.className = 'preview-overlay';
        this.overlay.addEventListener('click', () => this.hideActivePreview());
        document.body.appendChild(this.overlay);
    }
    
    attachEventListeners() {
        const cards = document.querySelectorAll('.card');
        
        cards.forEach(card => {
            const preview = card.querySelector('.card-preview');
            if (!preview) return;
            
            if (this.isMobile) {
                // モバイル：タップイベント（プレビュー表示）
                card.addEventListener('click', (e) => this.handleMobileClick(e, card, preview));
            } else {
                // デスクトップ：ホバーでプレビュー、クリックで記事に遷移
                card.addEventListener('mouseenter', (e) => {
                    // タイトルリンクのクリック時はプレビューを表示しない
                    if (e.target.tagName === 'A') return;
                    this.handleDesktopHover(card, preview);
                });
                card.addEventListener('mouseleave', (e) => this.handleDesktopLeave(card, preview));
                card.addEventListener('click', (e) => this.handleDesktopClick(e, card));
            }
        });
        
        // ESCキーでプレビューを閉じる
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideActivePreview();
            }
        });
    }
    
    handleMobileClick(event, card, preview) {
        // リンククリック時はプレビューではなく記事に移動
        if (event.target.tagName === 'A' || event.target.closest('a')) {
            return; // デフォルトのリンク動作を許可
        }
        
        event.preventDefault();
        
        // 既にプレビューが表示されている場合は閉じる
        if (preview.classList.contains('show')) {
            this.hidePreview(preview);
            return;
        }
        
        // 他のプレビューを閉じる
        this.hideActivePreview();
        
        // プレビューを表示
        this.showPreview(preview);
        this.activePreview = preview;
    }
    
    handleDesktopHover(card, preview) {
        // 遅延表示でちらつきを防止
        this.previewTimeout = setTimeout(() => {
            this.hideActivePreview();
            this.showPreview(preview);
            this.activePreview = preview;
            
            // プレビュー位置を調整
            this.adjustPreviewPosition(card, preview);
        }, 800);
    }
    
    handleDesktopLeave(card, preview) {
        // ホバー遅延をクリア
        if (this.previewTimeout) {
            clearTimeout(this.previewTimeout);
            this.previewTimeout = null;
        }
        
        // プレビューが表示されている場合は少し遅延して閉じる
        setTimeout(() => {
            if (this.activePreview === preview && !this.isHoveringPreview(preview)) {
                this.hidePreview(preview);
                this.activePreview = null;
            }
        }, 200);
    }
    
    handleDesktopClick(event, card) {
        // リンククリック時はデフォルトの動作を許可
        if (event.target.tagName === 'A' || event.target.closest('a')) {
            return;
        }
        
        // カード全体のクリックで記事に遷移
        const articleLink = card.querySelector('.card-title a');
        if (articleLink) {
            // 新しいタブで記事を開く
            window.open(articleLink.href, '_blank');
        }
    }
    
    showPreview(preview) {
        // プレビューをbodyの直下に移動（z-index競合を回避）
        if (preview.parentNode !== document.body) {
            document.body.appendChild(preview);
        }
        
        // 著者情報を表示/非表示の制御
        this.updateAuthorDisplay(preview);
        
        preview.style.display = 'block';
        
        // レイアウト計算を強制実行
        preview.offsetHeight;
        
        preview.classList.add('show');
        
        if (this.isMobile) {
            this.overlay.classList.add('show');
            document.body.style.overflow = 'hidden';
        }
    }
    
    updateAuthorDisplay(preview) {
        const authorElement = preview.querySelector('.preview-author');
        if (authorElement) {
            const authorInfo = authorElement.textContent.trim();
            
            if (authorInfo && authorInfo !== '') {
                // 著者情報がある場合は表示
                authorElement.style.display = 'inline';
                authorElement.textContent = `by ${authorInfo}`;
            } else {
                // 著者情報がない場合は非表示
                authorElement.style.display = 'none';
            }
        }
    }
    
    hidePreview(preview) {
        preview.classList.remove('show');
        
        setTimeout(() => {
            preview.style.display = 'none';
        }, 300);
        
        if (this.isMobile) {
            this.overlay.classList.remove('show');
            document.body.style.overflow = '';
        }
    }
    
    hideActivePreview() {
        if (this.activePreview) {
            this.hidePreview(this.activePreview);
            this.activePreview = null;
        }
    }
    
    adjustPreviewPosition(card, preview) {
        if (this.isMobile) return;
        
        const cardRect = card.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        // プレビューの仮サイズを取得
        const previewWidth = 400; // max-widthから
        const previewHeight = preview.scrollHeight || 300;
        
        // 横方向の位置調整
        let left = cardRect.left;
        if (left + previewWidth > viewportWidth - 20) {
            left = viewportWidth - previewWidth - 20;
        }
        if (left < 20) {
            left = 20;
        }
        
        // 縦方向の位置調整
        let top = cardRect.bottom + 8;
        if (top + previewHeight > viewportHeight - 20) {
            top = cardRect.top - previewHeight - 8;
            if (top < 20) {
                top = 20;
            }
        }
        
        // position: fixedで絶対位置に配置
        preview.style.left = left + 'px';
        preview.style.top = top + 'px';
        preview.style.right = 'auto';
        preview.style.bottom = 'auto';
        preview.style.marginTop = '0';
        preview.style.marginBottom = '0';
    }
    
    isHoveringPreview(preview, event = null) {
        // イベントオブジェクトが提供されていない場合は、要素のホバー状態をチェック
        if (!event) {
            return preview.matches(':hover');
        }
        
        const previewRect = preview.getBoundingClientRect();
        const mouseX = event.clientX;
        const mouseY = event.clientY;
        
        return mouseX >= previewRect.left && mouseX <= previewRect.right &&
               mouseY >= previewRect.top && mouseY <= previewRect.bottom;
    }
    
    handleResize() {
        window.addEventListener('resize', () => {
            const wasMobile = this.isMobile;
            this.isMobile = window.innerWidth <= 768;
            
            // モバイル⇔デスクトップ切り替え時にイベントリスナーを再設定
            if (wasMobile !== this.isMobile) {
                this.hideActivePreview();
                this.removeEventListeners();
                this.attachEventListeners();
            }
        });
    }
    
    removeEventListeners() {
        const cards = document.querySelectorAll('.card');
        cards.forEach(card => {
            card.replaceWith(card.cloneNode(true));
        });
    }
}

// プレビューを閉じるグローバル関数（HTMLから呼び出し用）
function hidePreview(event, cardId) {
    event.preventDefault();
    event.stopPropagation();
    
    const preview = document.getElementById(`preview-${cardId}`);
    if (preview && window.articlePreview) {
        window.articlePreview.hidePreview(preview);
        window.articlePreview.activePreview = null;
    }
}

// DOM読み込み完了後に初期化
document.addEventListener('DOMContentLoaded', () => {
    window.articlePreview = new ArticlePreview();
});

// ページ表示時にも初期化（ブラウザバック対応）
window.addEventListener('pageshow', () => {
    if (!window.articlePreview) {
        window.articlePreview = new ArticlePreview();
    }
});

/**
 * タグフィルタリング機能
 * 記事カードをタグに基づいてフィルタリング
 */
class TagFilter {
    constructor() {
        this.activeTag = 'all';
        this.cards = [];
        this.buttons = [];
        this.tagCounts = {};
        
        this.init();
    }
    
    init() {
        this.cards = Array.from(document.querySelectorAll('.card'));
        this.buttons = Array.from(document.querySelectorAll('.tag-filter-btn'));
        this.countTagsInCards();
        this.updateTagCounts();
        this.attachEventListeners();
    }
    
    countTagsInCards() {
        this.tagCounts = { 'all': this.cards.length };
        
        this.cards.forEach(card => {
            const tagsElement = card.querySelector('.preview-tags');
            if (tagsElement) {
                const tags = tagsElement.textContent.split(',').map(tag => tag.trim());
                tags.forEach(tag => {
                    if (tag && tag !== '') {
                        this.tagCounts[tag] = (this.tagCounts[tag] || 0) + 1;
                    }
                });
            }
        });
    }
    
    updateTagCounts() {
        this.buttons.forEach(button => {
            const tag = button.dataset.tag;
            const count = this.tagCounts[tag] || 0;
            
            if (tag === 'all') {
                button.textContent = `すべて (${this.tagCounts['all']})`;
            } else if (count > 0) {
                button.textContent = `${tag} (${count})`;
                button.style.display = 'inline-block';
            } else {
                button.style.display = 'none';
            }
        });
    }
    
    attachEventListeners() {
        this.buttons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const tag = button.dataset.tag;
                this.filterByTag(tag);
                this.updateActiveButton(button);
            });
        });
    }
    
    filterByTag(tag) {
        this.activeTag = tag;
        let visibleCount = 0;
        
        this.cards.forEach((card) => {
            const shouldShow = this.shouldShowCard(card, tag);
            
            if (shouldShow) {
                card.style.display = 'block';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
                visibleCount++;
            } else {
                card.style.display = 'none';
                card.style.opacity = '0';
                card.style.transform = 'translateY(-10px)';
            }
        });
        
        // セクション見出しを即座に更新
        this.updateSectionHeaders();
        
        // フィルタリング結果のフィードバック
        this.showFilterResults(tag, visibleCount);
        
        // フィルター状態を更新
        this.updateFilterStatus(tag, visibleCount);
    }
    
    updateSectionHeaders() {
        // 全てのセクション見出し（h2要素）を取得
        const headers = document.querySelectorAll('h2');
        
        headers.forEach(header => {
            // 見出しの次にある記事カードをカウント
            let visibleCardsInSection = 0;
            let nextElement = header.nextElementSibling;
            
            // 見出しの後にあるカードをチェック（次のh2まで）
            while (nextElement && nextElement.tagName !== 'H2') {
                if (nextElement.classList.contains('card')) {
                    const cardStyle = window.getComputedStyle(nextElement);
                    if (cardStyle.display !== 'none' && nextElement.style.opacity !== '0') {
                        visibleCardsInSection++;
                    }
                }
                nextElement = nextElement.nextElementSibling;
            }
            
            // 表示する記事がない場合は見出しを非表示
            if (visibleCardsInSection === 0) {
                header.style.display = 'none';
            } else {
                header.style.display = 'block';
            }
        });
    }
    
    
    shouldShowCard(card, tag) {
        if (tag === 'all') return true;
        
        const tagsElement = card.querySelector('.preview-tags');
        if (!tagsElement) return false;
        
        const cardTags = tagsElement.textContent.split(',').map(t => t.trim());
        return cardTags.includes(tag);
    }
    
    updateActiveButton(activeButton) {
        this.buttons.forEach(button => {
            button.classList.remove('active');
        });
        activeButton.classList.add('active');
    }
    
    showFilterResults(tag, count) {
        // 既存の結果表示を削除
        const existingResult = document.querySelector('.filter-result');
        if (existingResult) {
            existingResult.remove();
        }
        
        // フィルタリング結果を表示
        const resultElement = document.createElement('div');
        resultElement.className = 'filter-result';
        resultElement.style.cssText = `
            margin: 10px 0;
            padding: 8px 12px;
            background: #e7f3ff;
            border: 1px solid #b6e3ff;
            border-radius: 6px;
            font-size: 14px;
            color: #0969da;
            text-align: center;
        `;
        
        if (tag === 'all') {
            resultElement.textContent = `全ての記事 (${count}件) を表示中`;
        } else {
            resultElement.textContent = `「${tag}」でフィルタリング中 (${count}件)`;
        }
        
        // タグフィルターの後に挿入
        const filterContainer = document.querySelector('.tag-filter-container');
        if (filterContainer) {
            filterContainer.insertAdjacentElement('afterend', resultElement);
            
            // 3秒後に自動で削除
            setTimeout(() => {
                if (resultElement.parentNode) {
                    resultElement.remove();
                }
            }, 3000);
        }
    }
    
    updateFilterStatus(tag, visibleCount) {
        const filterStatus = document.getElementById('filterStatus');
        const filterStatusText = document.getElementById('filterStatusText');
        
        if (tag === 'all') {
            filterStatus.style.display = 'none';
        } else {
            filterStatus.style.display = 'flex';
            filterStatusText.textContent = `${tag}でフィルター中 (${visibleCount}件)`;
        }
    }
}

// DOM読み込み完了後にタグフィルターを初期化
document.addEventListener('DOMContentLoaded', () => {
    window.tagFilter = new TagFilter();
});

// ページ表示時にも初期化（ブラウザバック対応）
window.addEventListener('pageshow', () => {
    if (!window.tagFilter) {
        window.tagFilter = new TagFilter();
    }
});

/**
 * タグフィルターをクリア（すべて表示に戻す）
 */
function clearTagFilter() {
    if (window.tagFilter) {
        // 「すべて」ボタンを見つけてクリックをシミュレート
        const allButton = document.querySelector('.tag-filter-btn[data-tag="all"]');
        if (allButton) {
            window.tagFilter.filterByTag('all');
            window.tagFilter.updateActiveButton(allButton);
        }
    }
}

/**
 * タグフィルターの折りたたみ機能
 */
function toggleTagFilter() {
    const filterBar = document.getElementById('tagFilterBar');
    const toggleBtn = document.querySelector('.filter-toggle-btn');
    
    if (filterBar.classList.contains('collapsed')) {
        // 展開
        filterBar.classList.remove('collapsed');
        filterBar.classList.add('expanded');
        toggleBtn.classList.add('expanded');
    } else {
        // 折りたたみ
        filterBar.classList.remove('expanded');
        filterBar.classList.add('collapsed');
        toggleBtn.classList.remove('expanded');
    }
}

/**
 * ダークモード機能
 * システム設定の検出、ユーザー設定の永続化、テーマ切り替えを提供
 */
class ThemeManager {
    constructor() {
        this.themeKey = 'tech-news-theme';
        this.prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
        this.hideTimeout = null;
        this.isHovered = false;
        this.lastScrollY = window.scrollY;
        
        this.init();
    }
    
    init() {
        // フローティングボタンを作成
        this.createFloatingButton();
        
        // 保存されたテーマまたはシステム設定を適用
        this.applyInitialTheme();
        
        // テーマ切り替えボタンにイベントリスナーを追加
        this.attachEventListeners();
        
        // システム設定変更の監視
        this.watchSystemTheme();
        
        // 自動表示/非表示の設定
        this.setupAutoHide();
    }
    
    applyInitialTheme() {
        const savedTheme = localStorage.getItem(this.themeKey);
        
        if (savedTheme) {
            // 保存されたテーマを使用
            this.setTheme(savedTheme);
        } else {
            // システム設定に従う
            const systemTheme = this.prefersDark.matches ? 'dark' : 'light';
            this.setTheme(systemTheme, false); // localStorageには保存しない
        }
    }
    
    attachEventListeners() {
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }
    }
    
    createFloatingButton() {
        // 既存のボタンがあれば削除
        const existingButton = document.getElementById('theme-toggle');
        if (existingButton) {
            existingButton.remove();
        }
        
        // フローティングボタンを作成
        const button = document.createElement('button');
        button.id = 'theme-toggle';
        button.title = 'ダークモード切り替え';
        button.setAttribute('aria-label', 'テーマを切り替える');
        
        const icon = document.createElement('span');
        icon.id = 'theme-icon';
        icon.textContent = '🌙';
        
        const text = document.createElement('span');
        text.id = 'theme-text';
        text.textContent = 'ダークモード';
        
        button.appendChild(icon);
        button.appendChild(text);
        
        // ホバーイベントを追加
        button.addEventListener('mouseenter', () => {
            this.isHovered = true;
            this.showButton();
        });
        
        button.addEventListener('mouseleave', () => {
            this.isHovered = false;
            this.scheduleHide();
        });
        
        // bodyに追加
        document.body.appendChild(button);
    }
    
    watchSystemTheme() {
        // システムテーマ変更時の処理（ユーザーが明示的に設定していない場合のみ）
        this.prefersDark.addEventListener('change', (e) => {
            const savedTheme = localStorage.getItem(this.themeKey);
            if (!savedTheme) {
                // ユーザー設定がない場合のみシステム設定に従う
                const systemTheme = e.matches ? 'dark' : 'light';
                this.setTheme(systemTheme, false);
            }
        });
    }
    
    getCurrentTheme() {
        return document.documentElement.getAttribute('data-theme') || 
               (this.prefersDark.matches ? 'dark' : 'light');
    }
    
    setTheme(theme, saveToStorage = true) {
        // HTMLのdata-theme属性を設定
        if (theme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
        }
        
        // ボタンのテキストとアイコンを更新
        this.updateThemeButton(theme);
        
        // localStorage に保存（システム設定追従時は保存しない）
        if (saveToStorage) {
            localStorage.setItem(this.themeKey, theme);
        }
        
        // スムーズな切り替えアニメーション
        this.addTransitionClass();
    }
    
    toggleTheme() {
        const currentTheme = this.getCurrentTheme();
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        this.setTheme(newTheme);
        
        // 切り替えフィードバック
        this.showThemeChangeNotification(newTheme);
    }
    
    updateThemeButton(theme) {
        const themeIcon = document.getElementById('theme-icon');
        const themeText = document.getElementById('theme-text');
        
        if (themeIcon && themeText) {
            if (theme === 'dark') {
                themeIcon.textContent = '☀️';
                themeText.textContent = 'ライトモード';
            } else {
                themeIcon.textContent = '🌙';
                themeText.textContent = 'ダークモード';
            }
        }
    }
    
    addTransitionClass() {
        // 切り替えアニメーション用のクラスを一時的に追加
        document.documentElement.classList.add('theme-transition');
        
        setTimeout(() => {
            document.documentElement.classList.remove('theme-transition');
        }, 300);
    }
    
    showThemeChangeNotification(theme) {
        // 切り替え通知を表示（フィードバック）
        const notification = document.createElement('div');
        notification.className = 'theme-notification';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--card-bg);
            color: var(--text-color);
            border: 1px solid var(--border-color);
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            z-index: 10000;
            opacity: 0;
            transform: translateY(-20px);
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px var(--shadow-medium);
        `;
        
        const themeName = theme === 'dark' ? 'ダークモード' : 'ライトモード';
        notification.textContent = `${themeName}に切り替えました`;
        
        document.body.appendChild(notification);
        
        // アニメーション表示
        requestAnimationFrame(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateY(0)';
        });
        
        // 2秒後に削除
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(-20px)';
            
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }, 2000);
    }
    
    setupAutoHide() {
        // 初期表示（3秒後に自動で隠す）
        this.showButton();
        this.scheduleHide(3000);
        
        // スクロールイベントの監視
        let scrollTimeout;
        window.addEventListener('scroll', () => {
            // スクロール中は表示
            this.showButton();
            
            // スクロール停止をデバウンス検出
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                if (!this.isHovered) {
                    this.scheduleHide(1500); // スクロール停止1.5秒後に隠す
                }
            }, 150);
        });
        
        // マウス移動時の表示（画面端付近のみ）
        document.addEventListener('mousemove', (e) => {
            const rightEdgeThreshold = window.innerWidth - 150; // 右端150px
            const topEdgeThreshold = 150; // 上端150px
            
            if (e.clientX > rightEdgeThreshold && e.clientY < topEdgeThreshold) {
                this.showButton();
                this.scheduleHide(2000); // 2秒後に隠す
            }
        });
    }
    
    showButton() {
        const button = document.getElementById('theme-toggle');
        if (button) {
            button.style.opacity = '0.8';
            button.style.visibility = 'visible';
            button.style.pointerEvents = 'auto';
        }
        
        // 既存のタイマーをクリア
        if (this.hideTimeout) {
            clearTimeout(this.hideTimeout);
            this.hideTimeout = null;
        }
    }
    
    hideButton() {
        const button = document.getElementById('theme-toggle');
        if (button && !this.isHovered) {
            button.style.opacity = '0';
            button.style.pointerEvents = 'none';
            
            // 完全に非表示にする（アニメーション後）
            setTimeout(() => {
                if (button.style.opacity === '0') {
                    button.style.visibility = 'hidden';
                }
            }, 300);
        }
    }
    
    scheduleHide(delay = 2000) {
        if (this.hideTimeout) {
            clearTimeout(this.hideTimeout);
        }
        
        this.hideTimeout = setTimeout(() => {
            if (!this.isHovered) {
                this.hideButton();
            }
        }, delay);
    }
}

// DOM読み込み完了後にテーママネージャーを初期化
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
});

// ページ表示時にも初期化（ブラウザバック対応）
window.addEventListener('pageshow', () => {
    if (!window.themeManager) {
        window.themeManager = new ThemeManager();
    }
});