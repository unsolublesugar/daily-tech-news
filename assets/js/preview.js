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
                // モバイル：タップイベント
                card.addEventListener('click', (e) => this.handleMobileClick(e, card, preview));
            } else {
                // デスクトップ：ホバーイベント
                card.addEventListener('mouseenter', (e) => {
                    // タイトルリンクのクリック時はプレビューを表示しない
                    if (e.target.tagName === 'A') return;
                    this.handleDesktopHover(card, preview);
                });
                card.addEventListener('mouseleave', (e) => this.handleDesktopLeave(card, preview));
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
        }, 300);
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
    
    showPreview(preview) {
        preview.style.display = 'block';
        
        // レイアウト計算を強制実行
        preview.offsetHeight;
        
        preview.classList.add('show');
        
        if (this.isMobile) {
            this.overlay.classList.add('show');
            document.body.style.overflow = 'hidden';
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
        const previewRect = preview.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        // 横方向の調整
        if (cardRect.right + previewRect.width > viewportWidth - 20) {
            preview.style.left = 'auto';
            preview.style.right = '0';
        } else {
            preview.style.left = '0';
            preview.style.right = 'auto';
        }
        
        // 縦方向の調整（画面下端を超える場合）
        if (cardRect.bottom + previewRect.height > viewportHeight - 20) {
            preview.style.top = 'auto';
            preview.style.bottom = '100%';
            preview.style.marginTop = '0';
            preview.style.marginBottom = '8px';
        } else {
            preview.style.top = '100%';
            preview.style.bottom = 'auto';
            preview.style.marginTop = '8px';
            preview.style.marginBottom = '0';
        }
    }
    
    isHoveringPreview(preview) {
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