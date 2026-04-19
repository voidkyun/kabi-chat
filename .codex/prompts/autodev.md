---
description: Run this repository's autodev workflow
argument-hint: [REQUEST="<task or scope>"]
---

`[autodev]` モードとして依頼を処理してください。

作業開始前に、必ず以下を確認してください。

- `docs/agent-chat-rule/auto-develop.md`
- `docs/dev-workflow/autodev.md`
- 必要に応じて `docs/dev-workflow/code-review.md`

要求解釈と制約は `docs/agent-chat-rule/auto-develop.md` を優先し、実行フローは `docs/dev-workflow/autodev.md` に従ってください。

このスラッシュコマンドの後ろに続くテキストは、`[autodev]` を伴うユーザー要求として解釈してください。

ユーザーからの追加指示:

$ARGUMENTS
