#!/usr/bin/env bash
# PreToolUse(Bash) フック: mainブランチ上での git commit / merge / push を拒否する
# （.claude/rules/git-workflow.md「mainブランチへの直接コミット完全禁止」を機械的に担保）
set -u
input=$(cat)
cmd=$(printf '%s' "$input" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("command",""))' 2>/dev/null || true)

case "$cmd" in
  *"git commit"*|*"git merge"*|*"git push"*|*"git rebase"*) ;;
  *) exit 0 ;;
esac

branch=$(git -C "${CLAUDE_PROJECT_DIR:-.}" symbolic-ref --short -q HEAD 2>/dev/null || true)
if [ "$branch" = "main" ]; then
  echo "mainブランチへの直接コミット/マージ/pushは禁止です。feature/ fix/ docs/ ブランチを作成してから実行してください（.claude/rules/git-workflow.md）" >&2
  exit 2
fi
case "$cmd" in
  *"git push"*"--force"*|*"git push"*" -f "*|*"git push -f"*)
    echo "git push --force は明示的な指示がない限り禁止です（.claude/rules/ai-principles.md）" >&2
    exit 2 ;;
esac
exit 0
