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