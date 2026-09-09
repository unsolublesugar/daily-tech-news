---
name: start-work
description: 作業開始手順。Issueを作成し、mainを最新化してIssue番号付きブランチを切る。「作業を始めて」「Issueを作ってブランチを切って」「新しいタスクを開始」と言われたら使う。
argument-hint: <種別: feature|fix|docs> <作業内容の一言説明>
---

# 作業開始（Issue → ブランチ）

`.claude/rules/git-workflow.md` の必須手順1〜3を実行する。引数: `$ARGUMENTS`（種別と作業内容）。

## 手順

1. 種別を決める（feature=✨ enhancement / fix=🐛 bug / docs=📚 documentation / refactor=♻️ refactor / ci=🔧 ci / perf=🚀 performance）
2. Issue本文をスクラッチパッドに書く。「背景」「変更内容」「受け入れ条件」の3見出し
3. Issueを作成し、番号を控える
   ```bash
   gh issue create --title "<絵文字> <タイトル>" --label <label> --assignee @me --body-file <本文ファイル>
   ```
4. mainを最新化してブランチを作成
   ```bash
   git switch main && git pull origin main
   git switch -c <feature|fix|docs>/issue-<番号>-<短い英語スラッグ>
   ```
5. Issue番号・ブランチ名をユーザーに報告して、実装に入る

## 注意

- ラベルが無ければ `gh label create` で作る（色はルール記載の表に従う）
- 未コミットの変更がある状態でmainに切り替えない。先に `git stash` するか確認を取る
