---
name: create-pr
description: 現在のブランチからPull Requestを作成する。生成物の混入チェック、コミット、push、gh pr createまでを実行。「PRを作って」「プルリク出して」と言われたら使う。
disable-model-invocation: true
argument-hint: [Issue番号]
---

# Pull Request作成

`.claude/rules/git-workflow.md` の手順6〜8を実行する。引数 `$ARGUMENTS` はIssue番号（省略時はブランチ名 `*/issue-<番号>-*` から取る）。

## 手順

1. ブランチ名からIssue番号と種別を確認。mainなら中止して `/start-work` を案内
2. 生成物の混入チェック。差分があれば戻す（意図的な `data/summaries.json` 変更は確認を取る）
   ```bash
   git status --short
   git restore daily_news.md index.html rss.xml archives/ assets/partials/ 2>/dev/null
   ```
3. 未コミットの変更をコミット。メッセージは `<絵文字> <要約> (#<番号>)` 形式。末尾に会話で指定された Co-Authored-By 行を付ける
4. PR本文をスクラッチパッドに書く。先頭に `Closes #<番号>`（bugは `Fixes`）、続けて「変更内容」「変更理由」「テスト方法」。末尾に会話で指定された生成注記を付ける
5. push と PR作成
   ```bash
   git push -u origin <ブランチ>
   gh pr create --title "<絵文字> <タイトル> (#<番号>)" --assignee @me --label <label> --body-file <本文ファイル>
   ```
6. PRのURLを報告する

## チェック

- タイトル末尾の `(#番号)`、assignee、label、`Closes/Fixes` を満たしているか
- UI変更なら `/local-preview` で目視確認済みか。未確認ならPR本文にその旨を明記する
