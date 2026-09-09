---
name: release
description: GitHub Releaseを作成する。前回タグからの変更を集めてリリースノートを書き、タグ作成・push・gh release createを実行。「リリースして」「vX.Y.Zを切って」と言われたら使う。
disable-model-invocation: true
argument-hint: <vMAJOR.MINOR.PATCH>
---

# リリース作成

`.claude/rules/git-workflow.md` の「リリースノート運用」を実行する。引数 `$ARGUMENTS` はバージョン（省略時は変更内容から MINOR/PATCH を提案して確認を取る）。

## 手順

1. mainが最新であることを確認
   ```bash
   git switch main && git pull origin main
   gh release list --limit 1
   git log --oneline <前回タグ>..HEAD
   ```
2. 変更をマージ済みPRごとに分類し、リリースノートをスクラッチパッドに書く
   - 見出し: ✨新機能 / 🐛修正 / ♻️リファクタリング / 🔧設定 / 📚ドキュメント / 🚀パフォーマンス
   - 各行に PR番号 `(#N)` を付ける
   - 運用に影響する変更（Secrets追加、ワークフロー変更、出力形式変更）は `⚠️ Notes` に明記
3. ノート内容とバージョンをユーザーに提示して承認を得る
4. タグとリリース
   ```bash
   git tag -a vX.Y.Z -m "vX.Y.Z - 概要"
   git push origin vX.Y.Z
   gh release create vX.Y.Z --title "vX.Y.Z — 概要" --notes-file <ノートファイル> --latest
   ```
5. ReleaseのURLを報告する

## バージョン判定

- MAJOR: 既存の運用・設定を壊す（Secrets名変更、出力パス変更など）
- MINOR: 新機能・UIリニューアル・新フィード追加
- PATCH: バグ修正・文言調整
