/**
 * 今日のテックニュース - フロントエンド挙動
 *
 * - タブ切替（記事 / イベント / 書籍、スクロール位置をタブごとに保持）
 * - 記事行のインライン展開（クリック・タップのみ。ホバーでは何も起こさない）
 * - 絞り込みボトムシート（カテゴリ複数選択 = OR）
 * - テーマ切替（localStorage 永続化、未設定時は prefers-color-scheme）
 * - メディア目次チップのスムーススクロール
 * - フッター・絞り込みシートの中身は assets/partials/ から起動時に読み込んで差し込む
 */
(function () {
    'use strict';

    // document.currentScript は非同期処理に入ると null になるため、
    // 同期実行中のうちに自分自身の src（常に絶対URLに解決される）を控えておく
    var SCRIPT_SRC = document.currentScript ? document.currentScript.src : '';

    var THEME_KEY = 'tech-news-theme';
    var FILTER_KEY = 'tech-news-filter-tags';

    // ---------------------------------------------------------------
    // テーマ
    // ---------------------------------------------------------------

    function setupTheme() {
        var root = document.documentElement;
        var media = window.matchMedia('(prefers-color-scheme: dark)');
        var toggle = document.getElementById('theme-toggle');
        var icon = document.getElementById('theme-icon');

        function readStored() {
            try {
                return localStorage.getItem(THEME_KEY);
            } catch (e) {
                return null;
            }
        }

        function apply(theme, persist) {
            root.setAttribute('data-theme', theme);
            if (icon) {
                icon.textContent = theme === 'dark' ? '☀️' : '🌙';
            }
            if (toggle) {
                toggle.setAttribute('aria-label',
                    theme === 'dark' ? 'ライトモードに切り替える' : 'ダークモードに切り替える');
            }
            if (persist) {
                try {
                    localStorage.setItem(THEME_KEY, theme);
                } catch (e) { /* 保存できない環境では何もしない */ }
            }
        }

        var stored = readStored();
        apply(stored || (media.matches ? 'dark' : 'light'), false);

        if (toggle) {
            toggle.addEventListener('click', function () {
                var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
                apply(next, true);
            });
        }

        // ユーザーが明示的に選んでいない場合のみシステム設定に追従する
        var onSystemChange = function (event) {
            if (!readStored()) {
                apply(event.matches ? 'dark' : 'light', false);
            }
        };
        if (media.addEventListener) {
            media.addEventListener('change', onSystemChange);
        } else if (media.addListener) {
            media.addListener(onSystemChange);
        }
    }

    // ---------------------------------------------------------------
    // 固定ヘッダーの高さ（sticky なメディア目次・日付見出しのオフセット）
    // ---------------------------------------------------------------

    function setupHeaderHeight() {
        var header = document.querySelector('.app-header');
        if (!header) {
            return;
        }

        function update() {
            document.documentElement.style.setProperty(
                '--header-h', header.offsetHeight + 'px');
        }

        update();
        window.addEventListener('resize', update);
        if (window.ResizeObserver) {
            new ResizeObserver(update).observe(header);
        }
    }

    function headerOffset() {
        var header = document.querySelector('.app-header');
        var toc = document.querySelector('.tab-panel.is-active .media-toc');
        return (header ? header.offsetHeight : 0) + (toc ? toc.offsetHeight : 0);
    }

    // ---------------------------------------------------------------
    // タブ切替
    // ---------------------------------------------------------------

    function setupTabs() {
        var buttons = Array.prototype.slice.call(document.querySelectorAll('.tab-btn'));
        var panels = Array.prototype.slice.call(document.querySelectorAll('.tab-panel'));
        if (!buttons.length || !panels.length) {
            return;
        }

        var scrollPositions = {};
        var activeTab = 'articles';

        function activate(tab) {
            if (tab === activeTab) {
                return;
            }
            scrollPositions[activeTab] = window.scrollY;
            activeTab = tab;

            buttons.forEach(function (button) {
                var isActive = button.getAttribute('data-tab') === tab;
                button.classList.toggle('is-active', isActive);
                button.setAttribute('aria-selected', isActive ? 'true' : 'false');
            });

            panels.forEach(function (panel) {
                var isActive = panel.getAttribute('data-panel') === tab;
                panel.classList.toggle('is-active', isActive);
                panel.hidden = !isActive;
            });

            // 絞り込みは記事タブ専用
            var filterOpen = document.getElementById('filter-open');
            if (filterOpen) {
                filterOpen.hidden = tab !== 'articles';
            }

            window.scrollTo(0, scrollPositions[tab] || 0);
        }

        buttons.forEach(function (button) {
            button.addEventListener('click', function () {
                activate(button.getAttribute('data-tab'));
            });
        });
    }

    // ---------------------------------------------------------------
    // 記事行のインライン展開
    // ---------------------------------------------------------------

    function setupArticleRows() {
        var rows = Array.prototype.slice.call(document.querySelectorAll('.article-row'));

        rows.forEach(function (row) {
            function toggle() {
                var open = row.classList.toggle('is-open');
                row.setAttribute('aria-expanded', open ? 'true' : 'false');
            }

            row.addEventListener('click', function (event) {
                // リンク・ボタンのクリックは展開のトグルとして扱わない
                if (event.target.closest('a, button')) {
                    return;
                }
                toggle();
            });

            row.addEventListener('keydown', function (event) {
                if (event.target !== row) {
                    return;
                }
                if (event.key === 'Enter' || event.key === ' ' || event.key === 'Spacebar') {
                    event.preventDefault();
                    toggle();
                }
            });
        });
    }

    // ---------------------------------------------------------------
    // 共有ボタン
    // ---------------------------------------------------------------

    function setupShareButtons() {
        document.addEventListener('click', function (event) {
            var button = event.target.closest('.js-share');
            if (!button) {
                return;
            }
            event.preventDefault();

            var url = button.getAttribute('data-share-url') || location.href;
            var title = button.getAttribute('data-share-title') || document.title;

            if (navigator.share) {
                navigator.share({ title: title, url: url }).catch(function () { /* キャンセル */ });
                return;
            }

            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(url).then(function () {
                    var original = button.textContent;
                    button.textContent = 'コピーしました';
                    setTimeout(function () { button.textContent = original; }, 1500);
                }).catch(function () {
                    window.open(url, '_blank', 'noopener');
                });
                return;
            }

            window.open(url, '_blank', 'noopener');
        });
    }

    // ---------------------------------------------------------------
    // 絞り込みボトムシート
    // ---------------------------------------------------------------

    function setupFilterSheet() {
        var sheet = document.getElementById('filter-sheet');
        var openButton = document.getElementById('filter-open');
        if (!sheet || !openButton) {
            return;
        }

        var chips = Array.prototype.slice.call(sheet.querySelectorAll('.filter-chip'));
        var countLabel = document.getElementById('filter-count');
        var applyButton = document.getElementById('filter-apply');
        var clearButton = document.getElementById('filter-clear');
        var selected = restore();

        function restore() {
            try {
                var raw = sessionStorage.getItem(FILTER_KEY);
                return raw ? JSON.parse(raw) : [];
            } catch (e) {
                return [];
            }
        }

        function persist() {
            try {
                sessionStorage.setItem(FILTER_KEY, JSON.stringify(selected));
            } catch (e) { /* 保存できない環境では何もしない */ }
        }

        function syncChips() {
            chips.forEach(function (chip) {
                chip.classList.toggle('is-selected',
                    selected.indexOf(chip.getAttribute('data-tag')) !== -1);
            });
            if (applyButton) {
                applyButton.textContent = selected.length
                    ? selected.length + '件のカテゴリで絞り込む'
                    : 'この条件で表示';
            }
        }

        function syncHeader() {
            if (!countLabel) {
                return;
            }
            countLabel.textContent = selected.length ? String(selected.length) : '';
            countLabel.hidden = selected.length === 0;
        }

        function applyFilter() {
            var rows = Array.prototype.slice.call(document.querySelectorAll('.article-row'));
            rows.forEach(function (row) {
                if (!selected.length) {
                    row.hidden = false;
                    return;
                }
                var tags = (row.getAttribute('data-tags') || '').split(',');
                row.hidden = !selected.some(function (tag) {
                    return tags.indexOf(tag) !== -1;
                });
            });

            // 表示が0件になったメディアセクションは見出しごと隠す
            Array.prototype.slice.call(document.querySelectorAll('.media-section'))
                .forEach(function (section) {
                    var visible = section.querySelectorAll('.article-row:not([hidden])');
                    section.hidden = visible.length === 0;
                });

            syncHeader();
        }

        function open() {
            sheet.hidden = false;
            document.body.style.overflow = 'hidden';
        }

        function close() {
            sheet.hidden = true;
            document.body.style.overflow = '';
        }

        openButton.addEventListener('click', open);

        Array.prototype.slice.call(sheet.querySelectorAll('[data-close-filter]'))
            .forEach(function (element) {
                element.addEventListener('click', close);
            });

        chips.forEach(function (chip) {
            chip.addEventListener('click', function () {
                var tag = chip.getAttribute('data-tag');
                var index = selected.indexOf(tag);
                if (index === -1) {
                    selected.push(tag);
                } else {
                    selected.splice(index, 1);
                }
                persist();
                syncChips();
            });
        });

        if (applyButton) {
            applyButton.addEventListener('click', function () {
                applyFilter();
                close();
            });
        }

        if (clearButton) {
            clearButton.addEventListener('click', function () {
                selected = [];
                persist();
                syncChips();
                applyFilter();
            });
        }

        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape' && !sheet.hidden) {
                close();
            }
        });

        syncChips();
        applyFilter();
    }

    // ---------------------------------------------------------------
    // メディア目次のスムーススクロール
    // ---------------------------------------------------------------

    function setupTocScroll() {
        Array.prototype.slice.call(document.querySelectorAll('.toc-chip'))
            .forEach(function (chip) {
                chip.addEventListener('click', function (event) {
                    var id = chip.getAttribute('href');
                    if (!id || id.charAt(0) !== '#') {
                        return;
                    }
                    var target = document.getElementById(id.slice(1));
                    if (!target) {
                        return;
                    }
                    event.preventDefault();
                    window.scrollTo({
                        top: target.offsetTop - headerOffset(),
                        behavior: 'smooth'
                    });
                });
            });
    }

    // ---------------------------------------------------------------
    // ヘッダーの日付ナビゲーション（左＝新しい日付へ、右＝過去の日付へ）
    //
    // 各アーカイブページは生成時点のスナップショットで、まだ存在しない
    // 日付へのリンクは埋め込めない。archives/index.json を起動時に読み込んで
    // 前後の日付を都度計算する。
    // ---------------------------------------------------------------

    function setupDateNav() {
        var nav = document.querySelector('.tab-bar[data-current-date]');
        var newerLink = document.getElementById('date-nav-newer');
        var olderLink = document.getElementById('date-nav-older');
        if (!nav || !newerLink || !olderLink || !SCRIPT_SRC) {
            return;
        }

        var currentDate = nav.getAttribute('data-current-date');
        if (!currentDate) {
            return;
        }

        var assetPrefix = SCRIPT_SRC.replace(/assets\/js\/app\.js(?:[?#].*)?$/, '');

        function archiveUrl(date) {
            return assetPrefix + 'archives/' + date.slice(0, 4) + '/' + date.slice(5, 7) + '/' + date + '.html';
        }

        function apply(link, date) {
            if (date) {
                link.href = archiveUrl(date);
                link.classList.remove('is-disabled');
                link.removeAttribute('aria-disabled');
            } else {
                link.removeAttribute('href');
                link.classList.add('is-disabled');
                link.setAttribute('aria-disabled', 'true');
            }
        }

        fetch(assetPrefix + 'archives/index.json')
            .then(function (response) {
                return response.ok ? response.json() : [];
            })
            .then(function (days) {
                var dates = days.map(function (day) { return day.date; }).sort();
                var index = dates.indexOf(currentDate);
                if (index === -1) {
                    return;
                }
                apply(newerLink, index < dates.length - 1 ? dates[index + 1] : null);
                apply(olderLink, index > 0 ? dates[index - 1] : null);
            })
            .catch(function () {
                // 取得に失敗した場合は前後移動を無効のままにする
            });
    }

    // ---------------------------------------------------------------
    // アーカイブの年月タブ
    // ---------------------------------------------------------------

    function setupMonthTabs() {
        var tabs = Array.prototype.slice.call(document.querySelectorAll('.month-tab'));
        var panels = Array.prototype.slice.call(document.querySelectorAll('.month-panel'));
        if (!tabs.length || !panels.length) {
            return;
        }

        tabs.forEach(function (tab) {
            tab.addEventListener('click', function () {
                var month = tab.getAttribute('data-month');
                tabs.forEach(function (other) {
                    other.classList.toggle('is-active', other === tab);
                });
                panels.forEach(function (panel) {
                    panel.hidden = panel.getAttribute('data-month') !== month;
                });
                window.scrollTo(0, 0);
            });
        });
    }

    // ---------------------------------------------------------------
    // 全ページ共通パーツの読み込み（フッター・絞り込みシート）
    //
    // assets/partials/ 配下は全ページで内容が同一なため、ページに直接
    // 埋め込まず起動時に fetch して差し込む。中身に依存するセットアップ
    // （絞り込みシートのイベント登録など）は差し込み完了後に呼ぶ。
    // ---------------------------------------------------------------

    function loadPartial(elementId, partialFile, onLoaded) {
        var mount = document.getElementById(elementId);
        if (!mount || !SCRIPT_SRC) {
            return;
        }

        var assetPrefix = SCRIPT_SRC.replace(/assets\/js\/app\.js(?:[?#].*)?$/, '');
        fetch(assetPrefix + 'assets/partials/' + partialFile)
            .then(function (response) {
                return response.ok ? response.text() : '';
            })
            .then(function (html) {
                if (!html) {
                    return;
                }
                mount.innerHTML = html;
                if (onLoaded) {
                    onLoaded();
                }
            })
            .catch(function () {
                // 共通パーツの取得に失敗しても他の機能に影響させない
            });
    }

    function setupPartials() {
        loadPartial('footer-mount', 'footer.html');
        loadPartial('filter-sheet', 'filter_sheet.html', setupFilterSheet);
    }

    function init() {
        setupTheme();
        setupHeaderHeight();
        setupTabs();
        setupArticleRows();
        setupShareButtons();
        setupTocScroll();
        setupDateNav();
        setupMonthTabs();
        setupPartials();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
