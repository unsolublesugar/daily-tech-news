daily-tech-news の UI を刷新したい。デザインのハンドオフ資料一式を `design_handoff_daily_tech_news_ui/` に置いた。まず `design_handoff_daily_tech_news_ui/README.md` を最初から最後まで読んでから作業を始めること。

## 前提

- 同梱の `.dc.html` は **HTML で作られたデザインリファレンス**。そのままコピーして本番に入れるものではない。値（色・寸法・タイポ）だけを読み取り、このリポジトリの既存構成（Python + 文字列テンプレート + 素の CSS/JS、ビルドツールなし）で作り直す。React 等は導入しない。
- インラインスタイルで書かれているが、実装では **CSS クラス＋既存の CSS 変数**（`main.css` の `:root` / `[data-theme="dark"]`）に置き直す。README の Design Tokens が既存変数との対応表になっている。
- 採用案は **1a（トップ）/ 2a（アーカイブ）** とそのダーク版 **3a / 3b**。`1b` と `2b` は不採用・比較用なので実装しない。
- スクリーンショットは `design_handoff_daily_tech_news_ui/screenshots/` にある。

## やること（README「実装の進め方」に沿って）

1. `assets/css/main.css` の整理 — `.card` / `.card-preview` / `.preview-*` / `.tag-filter-*` / `.rss-card` / `.rss-info` / `#theme-toggle` を削除し、新レイアウト用クラスを追加。CSS 変数の構成は維持（新色は増やさない。細罫線 `#eef1f4` / ダーク `#21262d` のみ必要なら変数追加）
2. `assets/templates/` の再編 — `header.html` / `article_row.html` / `media_section.html` / `filter_sheet.html` / `footer.html` を作り、`card.html` `tag_filter.html` `navigation.html` `rss_info.html` を置き換え
3. `src/templates/template_manager.py` — `render_card()` を `render_article_row()` に置換（**サムネイル・著者情報・ホバープレビュー用 DOM をすべて撤去**。`data-tags` と要約は属性で持たせる）、`get_tag_filter_html()` を `get_filter_sheet_html()` に置換（カテゴリ一覧は `categorize_article()` の辞書キーから生成）
4. `src/generators/archive_generator.py` — 出力を「記事タブ（メディアごと3件固定）/ イベントタブ（**開催日時で日付グルーピング**、メディア別ではない）/ 書籍タブ」に分割。今日のハイライト3件の選定を追加（複数フィードに重複出現するものを優先、不足分は新着上位）
5. `src/config/archive_config.py` — `DISPLAY_PER_MEDIA = 3` を追加（取得件数 `MAX_ENTRIES_DEFAULT = 5` はハイライト選定に使うので据え置き）
6. `assets/js/preview.js` を削除し、`assets/js/app.js` を新規作成 — タブ切替 / 記事行のインライン展開 / 絞り込みボトムシート / テーマ切替 / メディア目次のスムーススクロール。**ホバーでプレビューを出す挙動は完全に廃止**（クリック・タップのみ）
7. アーカイブ — 年別・月別の中間ページをやめ、年月タブ＋カレンダーの1ページに集約。生成時に日別 JSON（`archives/index.json`: `{date, count, headline, top_categories[]}`）を書き出してページ生成に使う

## 特に守ってほしいこと

- ホバーで浮遊プレビューを出さない。詳細は行のクリックでインライン展開する
- 展開内容に **著者情報を出さない**（`by by by ...` と壊れて表示される不具合ごと撤去）。要約は RSS 本文の冒頭垂れ流しではなく、無ければ「概要なし」とだけ出す
- メディアごとの表示は **3件固定**。「もっと見る」は付けない
- タブやセクション見出しに **件数バッジを付けない**
- セクション見出しに favicon 画像を出さない（外部リクエスト削減）
- ダークの三次テキストは `#8b949e` 以上の明度を保つ（`#6e7681` は使わない）
- モバイル優先。PC は既存どおり `max-width: 800px` 中央寄せ
- 既存の生成フロー（`python3 fetch_news.py` → `index.html` / `daily_news.md` / `rss.xml` / `archives/`）と GitHub Actions の毎朝 JST 7:00 更新は壊さない

## 進め方

1〜7 を一度に全部やらず、**ステップごとにコミットして** 都度 `python3 fetch_news.py` を実行し、生成された `index.html` をブラウザで確認できる状態にしてから次に進んでほしい。既存の Markdown / RSS 出力に影響が出ていないかも各ステップで確認すること。
