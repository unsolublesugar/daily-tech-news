# Git ワークフロールール

## ブランチ戦略

- **mainブランチ**: 本番環境用、直接コミット完全禁止
- **featureブランチ**: 新機能開発用 (`feature/issue-番号-機能名`)
- **fixブランチ**: バグ修正用 (`fix/issue-番号-修正内容`)
- **docsブランチ**: ドキュメント更新用 (`docs/issue-番号-内容`)

## 開発ワークフロー ⚠️【必須手順】

1. **Issue作成**: 作業開始前に必ずIssueを作成
2. mainブランチに切り替え・最新pull
3. Issueに対応するブランチを作成（ブランチ名にIssue番号を含める）
4. 変更を実装・テスト
5. ブランチをリモートにプッシュ
6. Pull Requestを作成
7. レビュー・承認後にmainにマージ

## Issue作成ルール

```bash
# 機能追加
gh issue create --title "✨ 機能名: 簡潔な説明" --body "詳細な説明" --label enhancement --assignee @me

# バグ修正
gh issue create --title "🐛 バグ: 問題の説明" --body "再現手順と期待する動作" --label bug --assignee @me

# ドキュメント更新
gh issue create --title "📚 ドキュメント: 更新内容" --body "更新理由と詳細" --label documentation --assignee @me
```

### Issue作成チェックリスト
- [ ] タイトルに適切な絵文字プレフィックスが含まれているか (✨🐛📚♻️🔧🚀)
- [ ] 適切なラベルが設定されているか (enhancement/bug/documentation/refactor/ci/performance)
- [ ] アサイニーが設定されているか（`@me`）
- [ ] 本文に詳細な説明・受け入れ条件が記載されているか

## ブランチ作成手順

```bash
git checkout main
git pull origin main
git checkout -b feature/issue-番号-機能名
# または
git checkout -b fix/issue-番号-修正内容
```

### ブランチ命名チェックリスト
- [ ] `feature/issue-番号-機能名` または `fix/issue-番号-修正内容` の形式か
- [ ] Issue番号が正しく含まれているか
- [ ] mainブランチから最新pullしてからブランチを作成しているか

## Pull Request作成ルール

```bash
# 機能追加（Issue #13に対応）
gh pr create --title "✨ 機能名: 簡潔な説明 (#13)" --assignee @me --label enhancement --body "Closes #13\n\n詳細な説明"

# バグ修正（Issue #14に対応）
gh pr create --title "🐛 修正: 問題の説明 (#14)" --assignee @me --label bug --body "Fixes #14\n\n修正内容の詳細"
```

### PRチェックリスト
- [ ] タイトルに絵文字プレフィックスが含まれているか (✨🐛📚♻️🔧🚀)
- [ ] タイトル末尾にIssue番号 `(#番号)` が含まれているか
- [ ] assigneeが設定されているか（`@me`）
- [ ] 適切なlabelが設定されているか
- [ ] 本文先頭に `Closes #番号` または `Fixes #番号` が記載されているか

### PR本文テンプレート

```markdown
## 変更内容
- 具体的な変更点を箇条書き

## 変更理由
- なぜこの変更が必要か

## テスト方法
- 動作確認手順
```

## タイトル絵文字プレフィックス

| 絵文字 | 用途 |
|--------|------|
| ✨ | 新機能 |
| 🐛 | バグ修正 |
| 📚 | ドキュメント |
| ♻️ | リファクタリング |
| 🔧 | 設定・環境 |
| 🚀 | パフォーマンス改善 |

## ラベル管理

適切なラベルが存在しない場合は新規作成：

```bash
gh label create "ラベル名" --description "説明" --color "カラーコード"
```

| ラベル | カラー |
|--------|--------|
| `enhancement` | `#a2eeef` |
| `bug` | `#d73a49` |
| `documentation` | `#0075ca` |
| `performance` | `#0e8a16` |
| `refactor` | `#fbca04` |
| `ci` | `#6f42c1` |
