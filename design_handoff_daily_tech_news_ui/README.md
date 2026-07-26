# Handoff: daily-tech-news UI 刷新（トップページ／アーカイブ／ダークモード）

## Overview

`unsolublesugar/daily-tech-news`（Python で毎朝生成する静的サイト）の見た目と情報整理を刷新する。目的は3つ。

1. **1ページの表示量を減らす** — 全メディア5件（イベントは各10件）を無条件に縦積みしていた構成をやめ、メディアごと **3件固定**、イベントと書籍は別タブへ分離する。
2. **ホバー式フロートプレビューの廃止** — 一覧を眺めているだけで `card-preview` が出る挙動をやめ、**行のタップ／クリックでインライン展開**に置き換える。展開内容も OGP／RSS の本文冒頭ではなく「読むか判断するための情報」に限定する（著者表示は撤去 = `by by by ...` 不具合の解消）。
3. **アーカイブの導線短縮** — 年 → 月 → 日 と3ページたどる Markdown 変換ページを、年月タブ＋カレンダーの1ページに集約する。

採用案は **1a（トップ）／2a（アーカイブ）** と、そのダーク版 **3a／3b**。

## About the Design Files

このバンドルに含まれる `.dc.html` は **HTML で作られたデザインリファレンス（プロトタイプ）** であり、そのまま本番に投入するコードではない。意図した見た目と挙動を示すもので、実装タスクは「このデザインを対象コードベースの既存環境で作り直すこと」。

このプロジェクトの対象環境は **Python + 文字列テンプレート + 素の CSS/JS** で、ビルドツールも JS フレームワークもない。したがって実装は以下のファイル群への変更になる（React 等を新規導入する必要はない）。

- `assets/css/main.css` — スタイル本体（CSS 変数でライト／ダーク切替）
- `assets/templates/*.html` — `{{key}}` を `str.replace` で埋めるだけの素朴なテンプレート
- `src/templates/template_manager.py` — カード／ナビ／フッター／タグフィルターの HTML 生成、`categorize_article()` によるタグ付与
- `src/generators/archive_generator.py` — セクション見出し `<h2>{feed_name}</h2>` の出力、アーカイブ Markdown→HTML 変換
- `assets/js/preview.js` — ホバープレビューの実装（**廃止対象**。タップ展開＋タブ切替＋絞り込みシートに置き換え）
- `src/config/archive_config.py` — `MAX_ENTRIES_DEFAULT = 5` / `MAX_ENTRIES_EVENTS = 10`

なおプロトタイプはインラインスタイルで書かれている（デザインツール側の制約）。実装では **CSS クラス＋既存の CSS 変数** に置き直すこと。値はすべて下記 Design Tokens に対応している。

## Fidelity

**High-fidelity。** 色・タイポグラフィ・余白・角丸・状態変化は最終値として扱ってよい。ダーク値は既存 `main.css` の `[data-theme="dark"]` トークンをそのまま使っている（新色は追加していない）。

ダミーであるのはコンテンツのみ（記事タイトルは 2026-07-26 の実データ、時刻・件数・カレンダーの出現日は表示確認用のサンプル）。

## Screens / Views

### 1. トップページ `index.html`（プロトタイプ id `1a` / ダーク `3a`）

**Purpose**: 朝いちで「今日読むもの」を数十秒でトリアージする。

**Layout**（外枠）

- モバイル基準で設計。PC は既存どおり `body { max-width: 800px; margin: 0 auto; }` を維持。
- 縦は 3 レイヤー: **固定ヘッダー（sticky）** → **スクロール領域** → （モーダル時のみ）**絞り込みボトムシート**。
- 左右パディングはヘッダー・本文とも `16px`、ヘッダー内タブ列のみ `12px`。

**固定ヘッダー**（`position: sticky; top: 0`、背景 `--bg-color`、下辺 `1px solid --border-color`）

- 1段目: `padding: 12px 16px 8px;` の `display:flex; justify-content:space-between; align-items:center`
  - 左: サイト名 `今日のテックニュース` — 15px / 700 / `letter-spacing: -0.01em` / `--heading-color`、その右に日付 `7/26 (日)` — 12px / `--text-secondary` / `font-variant-numeric: tabular-nums`（`👨‍💻` 絵文字と `(2026-07-26)` の長い `<h1>` は廃止）
  - 右: `絞り込み` ボタン（高さ 30px / パディング 0 10px / 角丸 8px / `1px solid --border-color` / 12px 600）＋ テーマ切替ボタン（30×30 / 同枠 / 絵文字 🌙・☀️）。選択中カテゴリ数があればボタン内に 11px `--text-secondary` で件数を出す
  - hover: 背景 `--button-hover`
- 2段目: タブ `記事 / イベント / 書籍`（`display:flex; gap:4px; padding: 0 12px 10px;`）
  - 各タブ: 高さ 32px / パディング 0 14px / 角丸 8px / 13px 600 / border なし
  - 選択: 背景 `#1f2328`（ダーク `#e6edf3`）、文字 `#ffffff`（ダーク `#0d1117`）
  - 非選択: 背景 `#f6f8fa`（ダーク `#161b22`）、文字 `--text-secondary`
  - **件数バッジは付けない**（3件固定なので情報価値がないため削除済み）

**スクロール領域 / 記事タブ**

1. **メディア目次チップ**（sticky、ヘッダー直下 `top: 0`、背景 `rgba(255,255,255,0.94)`／ダーク `rgba(13,17,23,0.94)` ＋ `backdrop-filter: blur(8px)`、下辺 1px `#eef1f4`／ダーク `#30363d`）
   - 横スクロール（`overflow-x: auto`）。**スクロールバーは非表示**: `scrollbar-width: none; -ms-overflow-style: none;` ＋ `::-webkit-scrollbar { width:0; height:0; display:none; }`
   - チップ: 高さ 26px / パディング 0 10px / 角丸 13px / 12px / `1px solid --border-color` / 文字 `--text-secondary`、hover で枠と文字を `--link-color`
   - ラベルは `はてなブックマーク - IT（人気）` → `はてブIT（人気）` のように短縮（実装では表示名マップを持つ）
   - クリックで該当セクションへスクロール（`scrollIntoView` は使わず `window.scrollTo({ top: el.offsetTop - headerH, behavior:'smooth' })`）
2. **今日のハイライト**（`padding: 18px 16px 4px;`）
   - 見出し行: `今日のハイライト` 13px 700 `--heading-color` ＋ 補足 `複数メディアで話題` 11px `--text-secondary`
   - カード3枚（`display:flex; flex-direction:column; gap:10px`）: `padding:14px` / 角丸 12px / `1px solid --border-color` / 背景 `--bg-color`（ダーク `#161b22`）/ hover で枠 `--link-color`
   - 中身は `display:flex; gap:12px` の2カラム: 順位 18px 800 `--link-color`（幅 22px、tabular-nums）／ 右にタイトル 16px 700 line-height 1.45 `--heading-color` `text-wrap: pretty` ＋ メタ 12px `--text-secondary`（例 `gihyo.jp ・ 他3メディアで言及 ・ 8:00`）
   - **選定ロジック（実装側で必要）**: 同一 URL／類似タイトルが複数フィードに出現するものを優先し、上位3件。実装が難しければ暫定で「はてブ人気 ∩ 他メディア」→ 不足分は新着上位で埋める
3. **メディアセクション**（`MEDIA` ごとに繰り返し、`padding: 22px 16px 0;`）
   - 見出し: メディア名 14px 700 `--heading-color`、下辺 `2px solid #1f2328`（ダーク `#e6edf3`）、`padding-bottom: 8px`。**favicon 画像・件数・「サイトへ」リンクは無し**（現行の `<h2><img src="...favicon.ico">` は廃止）
   - 記事行（3件固定）: `padding: 12px 0`、下辺 `1px solid #eef1f4`（ダーク `#21262d`）、`cursor: pointer`
     - 1行目: タイトル 14px 600 line-height 1.5 `--heading-color`（**リンク色にしない**）＋ 右端に時刻 11px `#8b949e` tabular-nums（`5:20` / `昨日` / `2日前`）
     - 2行目: カテゴリタグ（`categorize_article()` の結果）を最大2つ。高さ 18px / パディング 0 6px / 角丸 4px / 11px 500 / 背景 `#f6f8fa`（ダーク `#21262d`）/ 文字 `--text-secondary`
     - 展開時（下記 Interactions）: 背景 `#f6f8fa`（ダーク `#21262d`）/ 角丸 8px / `padding: 10px 12px` の枠内に、要約 12px line-height 1.6 `--text-secondary` ＋ ボタン2つ（`記事を読む ↗` = 背景 `--link-color` / 白文字 / 高さ30px / 角丸6px / 12px 600、`共有` = 背景 `--bg-color` / `1px solid --border-color`）
   - **「もっと見る」ボタンは無し**（3件固定）
4. **フッター**（`padding: 28px 16px 24px;`）
   - RSS 行: `display:flex; justify-content:space-between; align-items:center` / `padding:14px 16px` / 角丸 12px / `1px solid --border-color` / 背景 `#f6f8fa`（ダーク `#161b22`）。左に `RSSで購読` 13px 700 ＋ `毎朝 JST 7:00 更新` 11px `--text-secondary`、右に `📡 登録` ボタン（高さ30px / 角丸8px / 枠 1px）
   - リンクタイル: `display:grid; grid-template-columns:1fr 1fr; gap:8px`。各タイル `padding:12px 14px` / 角丸12px / `1px solid --border-color`、1行目 `📚 アーカイブ` / `📁 GitHub` 13px 700 `--heading-color`、2行目 `過去のニュース` / `ソースとフィード設定` 11px `#8b949e`
   - クレジット: 中央 `Built by @unsoluble_sugar` 11px、`@...` のみ `--text-secondary` 600
   - 既存の `.rss-card`（48px の 📡 アイコン付き中央寄せカード）と `.rss-info` ボックスは **両方廃止**（重複しているため上記1つに統合）

**イベントタブ**

- 冒頭に説明 13px `--text-secondary`: 「connpass・TECH PLAY の直近イベント。日付順にまとめて、開催が近いものから表示します。」
- **日付ごとにグルーピング**（現行のメディア別 10件ずつ = 20件ベタ置きをやめる）。日付見出しは sticky、12px 700 `--link-color`、下辺 1px
- 行: 左に開催時刻 11px `#8b949e`（幅 44px、tabular-nums）／右にタイトル 14px 600 line-height 1.45 ＋ メタ 11px `--text-secondary`（`connpass ・ 東京都北区`）
- 実装メモ: connpass / TECH PLAY のフィードから **開催日時** を取得して昇順ソート（現行は取得時刻順）。TECH PLAY 側で開催日時が取れない場合は「日付不明」グループを末尾に置く

**書籍タブ**

- O'Reilly Japan 近刊5件。行は `display:flex; justify-content:space-between` で、左にタイトル 14px 600、右に `9/12 発売` 11px `#8b949e`

**絞り込みボトムシート**（記事タブのヘッダー「絞り込み」から）

- オーバーレイ `rgba(15,23,42,0.35)`、シートは下寄せ・角丸 `18px 18px 0 0`・`max-height: 78%`・影 `0 -8px 32px rgba(15,23,42,0.18)`
- ヘッダー: `絞り込み` 15px 700 ＋ 右に `×` 20px
- 本文: グループ見出し 11px 700 `#8b949e` `letter-spacing: .06em` `text-transform: uppercase`（`よく使う` / `開発・運用` / `専門・その他`）＋ チップ（高さ30px / 角丸15px / 12px 600 / 枠 `1px solid #d1d9e0`）。選択時は背景・枠 `--link-color`、文字白
- フッター: `クリア`（枠線ボタン、flex 1）＋ `この条件で表示` / `N件のカテゴリで絞り込む`（背景 `--link-color`、白文字、flex 2）、高さ 40px / 角丸 10px
- **現行の `tag_filter.html`（26個のチップを常時 DOM に置く折りたたみグリッド）は廃止**。カテゴリ一覧は `template_manager.categorize_article()` の辞書キーから生成する

### 2. アーカイブ `archives/index.html`（プロトタイプ id `2a` / ダーク `3b`）

**Purpose**: 過去の日付にすばやく飛ぶ。現状は年 → 月 → 日で3ページ、しかも `main.css` を読み込んでいない素の変換 HTML（比較用に `2b` として再現してある）。

**Layout**

- ヘッダー: 戻る `←`（30×30 / 角丸8px / 枠1px）＋ `アーカイブ` 15px 700、右端に総数 `全 412 日分` 11px `#8b949e`
- 年月タブ: 横スクロール（スクロールバー非表示）、`2026年7月 / 6月 / 5月 … / 2025年`。高さ30px / 角丸15px / 13px 600、選択時 背景 `#1f2328`（ダーク `#e6edf3`）文字白（ダーク `#0d1117`）
- カレンダー（`padding: 16px`）
  - 曜日ヘッダー: `grid-template-columns: repeat(7, 1fr); gap:4px`、10px 700 `#8b949e` 中央寄せ
  - 日セル: 同グリッド、`aspect-ratio: 1/1`、角丸8px、12px 600 tabular-nums
    - 記事あり: 背景 `#ddf4ff` / 文字 `#0969da` / 枠 `#b6e3ff`（ダーク: 背景 `rgba(56,139,253,0.15)` / 文字 `#58a6ff` / 枠 `#30363d`）
    - 最新日: 背景 `#0969da` / 文字 `#ffffff`（ダーク: 背景 `#58a6ff` / 文字 `#0d1117`）
    - 記事なし: 背景 `--bg-color` / 文字 `#d1d9e0`（ダーク `#30363d`）/ 枠 `#eef1f4`（ダーク `#21262d`）
  - 凡例: 10px の色見本 ＋ `記事あり` / `最新` 11px `#8b949e`
- 日付リスト（`padding: 4px 16px 24px`）
  - 見出し `2026年7月の一覧` 12px 700、下辺 `2px solid #1f2328`（ダーク `#e6edf3`）
  - 行: 左に日 15px 700 tabular-nums ＋ 曜日 10px `#8b949e`（幅 52px）／右にその日の主要見出し 13px 600 line-height 1.5 ＋ メタ 11px `#8b949e`（`50本 ・ AI・機械学習 / セキュリティ が多め`）
  - 下辺 `1px solid #eef1f4`（ダーク `#21262d`）
- 実装メモ: 年別・月別の中間ページは廃止（既存 URL は残して 1ページへリダイレクト or リンク差し替え）。日付ごとの「主要見出し」と本数は、アーカイブ生成時に日別 JSON（`archives/index.json`: `{date, count, headline, top_categories[]}`）を書き出してページ生成に使うのが素直。`convert_markdown_to_html()` の素朴な行変換（`- [x](y) | [z](w)` の後半リンクが落ちる、`[← 戻る](..)` が生テキストで出る）はこの経路では使わなくなる

### 3. ダークモード（`3a` / `3b`）

既存の `[data-theme="dark"]` トークンのみで構成。ライトとの差分は以下だけ。

- 面 `--bg-color: #0d1117`、カード／シート `--card-bg: #161b22`、ボタン面 `--button-bg: #21262d`
- 罫線 `--border-color: #30363d`、行間の細い区切りは `#21262d`
- 本文 `--text-color: #e6edf3`、見出し `--heading-color: #f0f6fc`、メタ／三次テキストは **すべて `--text-secondary: #8b949e`**（11px 以下でもこれ以上暗くしない。`#6e7681` はコントラスト不足のため使用禁止）
- アクセント `--link-color: #58a6ff`
- セクション見出しの下線はライト `#1f2328` → ダーク `#e6edf3`
- 現行の右上フローティング `#theme-toggle`（`position: fixed`、初期 `opacity: 0; visibility: hidden`）は廃止し、**ヘッダー内の 30×30 ボタン**に統合する

## Interactions & Behavior

| 対象 | 挙動 |
|---|---|
| 記事行 | クリック／タップで**インライン展開**（同時に複数開けてよい）。もう一度で閉じる。ホバーでは何も起こさない |
| 展開の中身 | 要約テキスト＋`記事を読む ↗`（`target="_blank" rel="noopener"`）＋`共有`。**著者行は出さない**（`by by by ...` の不具合ごと撤去）。要約は本文冒頭の垂れ流しではなく、無い場合は「概要なし」とだけ出す |
| タブ | `記事 / イベント / 書籍` を切替。スクロール位置はタブごとに保持 |
| メディア目次チップ | 該当セクションへスムーススクロール（sticky ヘッダー分オフセット） |
| 絞り込みシート | ヘッダーのボタンで開く。オーバーレイ／`×`／`この条件で表示` で閉じる。カテゴリは複数選択（OR）。選択中は記事行を `data-tags` でフィルタ、0件のメディアセクションは見出しごと隠す |
| テーマ切替 | `document.documentElement.dataset.theme` を `light`/`dark` に切替、`localStorage` に保存。未設定時は `prefers-color-scheme` に従う（現行実装のまま） |
| カレンダー | 記事のある日のみリンク。年月タブで表示月を切替 |
| トランジション | 展開は `max-height`/`opacity` で 0.2s ease。既存の `transition: all 0.2s ease` の粒度に合わせる。ホバーの `transform: translateY(-2px)` は廃止（カードが消えたため） |
| レスポンシブ | ~800px までは1カラムのまま横幅追従。801px 以上は `max-width: 800px` 中央寄せ。タップ領域は最低 44px（記事行は上下 12px + 2行で満たす） |

## State Management

クライアント側（`assets/js/` の素の JS、フレームワーク不要）で持つ状態は5つ。

- `activeTab`: `'articles' | 'events' | 'books'` — 既定 `'articles'`
- `openItems`: `Set<cardId>` — 展開中の記事行。`cardId` は既存の `template_manager.generate_card_id()`（MD5 先頭8桁）を流用
- `selectedTags`: `string[]` — 絞り込みシートの選択カテゴリ。`sessionStorage` に保持すると再訪時に親切（任意）
- `filterSheetOpen`: `boolean`
- `theme`: `'light' | 'dark'` — `localStorage` 永続化（既存挙動を踏襲）

データ取得は不要（生成時にすべて HTML へ焼き込む）。要約テキストは既存どおり `data-*` 属性に埋め、展開時に表示するだけでよい。

## Design Tokens

すべて `main.css` の既存変数に対応。**新しい色は増やしていない**（`#eef1f4` の細罫線のみ新規、必要なら `--border-subtle` として追加）。

**Color — Light**

| 用途 | 値 | 既存変数 |
|---|---|---|
| 背景 | `#ffffff` | `--bg-color` |
| 面（カード・シート・チップ） | `#f6f8fa` / `#f8f9fa` | `--card-bg` |
| 罫線 | `#e1e5e9` | `--border-color` |
| 細罫線（行区切り） | `#eef1f4` | 新規（任意） |
| 本文 | `#333333` | `--text-color` |
| 見出し | `#1f2328` | `--heading-color` |
| 二次テキスト | `#656d76` | `--text-secondary` |
| 三次テキスト（時刻など） | `#8b949e` | — |
| アクセント／リンク | `#0969da` / hover `#0860ca` | `--link-color` / `--link-hover` |
| カレンダー: 記事あり | 面 `#ddf4ff` / 枠 `#b6e3ff` | — |

**Color — Dark**（`[data-theme="dark"]`）

背景 `#0d1117` / 面 `#161b22` / ボタン面 `#21262d` / 罫線 `#30363d` / 細罫線 `#21262d` / 本文 `#e6edf3` / 見出し `#f0f6fc` / 二次・三次テキスト `#8b949e` / アクセント `#58a6ff`（hover `#79c0ff`）/ カレンダー記事あり `rgba(56,139,253,0.15)`

**Typography**（フォントは現行のまま `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`）

| 役割 | size / weight / line-height |
|---|---|
| サイト名 | 15 / 700 / 1.3（`letter-spacing: -0.01em`） |
| セクション見出し | 14 / 700 / 1.4 |
| ハイライトタイトル | 16 / 700 / 1.45 |
| 記事タイトル | 14 / 600 / 1.5 |
| アーカイブ日付 | 15 / 700 / 1.2（tabular-nums） |
| 補助・メタ | 12 / 400–500 / 1.5 |
| タグ・時刻・キャプション | 11 / 500 / 1.4 |
| 曜日ヘッダー | 10 / 700 / 1 |

長いタイトルには `text-wrap: pretty; overflow-wrap: break-word;`。数字は `font-variant-numeric: tabular-nums`。

**Spacing**: 4 / 6 / 8 / 10 / 12 / 14 / 16 / 18 / 22 / 28 px（左右基準は 16px）

**Radius**: 4（タグ）/ 6（小ボタン）/ 8（ボタン・展開枠）/ 12（カード・タイル）/ 13–15（チップ）/ 18（シート上端）

**Shadow**: カードは影なし（枠線のみ）。ボトムシート `0 -8px 32px rgba(15,23,42,0.18)`。オーバーレイ `rgba(15,23,42,0.35)`

## Assets

- 追加アセットなし。**既存の favicon 取得（`https://zenn.dev/favicon.ico` 等の外部読み込み）はセクション見出しから削除**したので、その分の外部リクエストが減る
- 絵文字（📚 📁 📡 🌙 ☀️）はテキストとして使用。現行の `👨‍💻` `🏷️` `🎨` はヘッダーの整理に伴い不使用
- X ロゴ SVG（`assets/images/x-logo/logo.svg`）はヘッダーから外し、共有アクションは記事展開時の `共有` ボタンに移動

## Files

| ファイル | 内容 |
|---|---|
| `Redesign.dc.html` | 採用デザイン。Turn 3 = ダーク（`3a` トップ / `3b` アーカイブ）、Turn 2 = アーカイブ（`2a` 新案 / `2b` 現状再現）、Turn 1 = トップ（`1a` 採用案 / `1b` 不採用の横断タイムライン案） |
| `Current UI.dc.html` | 現行トップページの忠実な再現（比較用）。現行のホバープレビュー挙動もそのまま再現してある |
| `github.md` | 参照元リポジトリと画面 → ソースファイルの対応表 |
| `screenshots/1a-top-light.png` | トップ（ライト・採用案） |
| `screenshots/2a-archive-light.png` | アーカイブ（ライト・採用案） |
| `screenshots/3a-top-dark.png` | トップ（ダーク） |
| `screenshots/3b-archive-dark.png` | アーカイブ（ダーク） |
| `screenshots/2b-archive-current.png` | 現状のアーカイブ（比較用） |

ブラウザで直接開ける。`Redesign.dc.html` 内はインラインスタイル＋小さな JS で、レイアウト値はすべて上記トークンと一致している。

## 実装の進め方（推奨順）

1. `assets/css/main.css` を新トークン構成に整理（`.card` / `.card-preview` / `.tag-filter-*` / `.rss-card` / `.rss-info` / `#theme-toggle` の削除、新クラスの追加）
2. `assets/templates/` に `header.html` / `article_row.html` / `media_section.html` / `filter_sheet.html` / `footer.html` を用意し、`card.html` `tag_filter.html` `navigation.html` `rss_info.html` を置き換え
3. `template_manager.py`: `render_card()` → `render_article_row()`（サムネイル・著者・プレビュー DOM を撤去、`data-tags` と要約を属性に）、`get_tag_filter_html()` → `get_filter_sheet_html()`
4. `archive_generator.py`: `_process_entries()` を「記事3件固定 / イベントは日付グルーピング / 書籍は別タブ」に分割出力。ハイライト選定を追加
5. `archive_config.py`: 表示件数の定数を `DISPLAY_PER_MEDIA = 3` として追加（取得件数 5 はそのままでよい ― ハイライト選定に使える）
6. `assets/js/preview.js` を破棄し、`assets/js/app.js`（タブ・展開・絞り込み・テーマ・スムーススクロール）を新規作成
7. アーカイブ: 日別 JSON の書き出し ＋ カレンダーページ生成
