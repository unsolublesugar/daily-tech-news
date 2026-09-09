---
name: local-preview
description: ローカルでニュースを生成しブラウザで動作確認する。fetch_news.py実行→http.server起動→index.html/archivesを確認→生成物の差分を戻す。「ローカルで確認」「プレビューして」「動作確認」と言われたら使う。UI変更時は必須。
argument-hint: [--with-ai] [--port 8000]
---

# ローカル動作確認

`$ARGUMENTS` に `--with-ai` があればAI要約付きで生成する（`LLM_API_KEY` が環境に必要。件数は `MAX_SUMMARIZE_PER_RUN=3` に絞る）。

## 手順

1. 生成
   ```bash
   python3 fetch_news.py                                   # 通常
   MAX_SUMMARIZE_PER_RUN=3 python3 fetch_news.py           # --with-ai（LLM_API_KEY設定済み前提）
   ```
   標準出力のフィードごとの件数・エラー・AI要約の統計（cached/generated/failed/skipped）を確認する
2. サーバー起動（バックグラウンド）と疎通確認
   ```bash
   python3 -m http.server 8000
   curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/
   open http://localhost:8000/
   ```
3. 確認ポイント
   - `index.html`: 各フィードのカード、AI要約の展開部（--with-ai時）、フィルタ、ダーク/ライト表示
   - `archives/index.html`: カレンダー・年月タブ・当日分へのリンク
   - `rss.xml` / `daily_news.md`: 文字化け・空セクションが無いか
   - ブラウザのコンソールにJSエラーが無いか
4. 終了後、生成物の差分を戻す（ソース変更だけを残す）
   ```bash
   git restore daily_news.md index.html rss.xml archives/ assets/partials/
   git status --short
   ```
   `data/summaries.json` はキャッシュ更新が乗る。PRに含めるべきか判断できなければ戻す

## 注意

- `slack_message.json` / `thumbnail_cache.json` はgitignore済みなので放置でよい
- 外部フィードの取得失敗は環境要因のことが多い。同じフィードが連続で失敗する場合だけ報告する
