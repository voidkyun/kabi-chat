# Repo Guidance

このリポジトリの AI 向けルールの正本`docs/`ディレクトリです。

作業前に該当ドキュメントを確認し、実装後はコード・README・docs の整合性を保ってください。

Backend 関連のコマンド実行は必ず Docker 経由で行ってください。`python`、`pytest`、`poetry` をホストで直接実行せず、`docs/dev-workflow/backend.md` に従って `docker compose exec app ...` または `docker compose run --rm app ...` を使います。

`AGENTS.md` には詳細ルールを重複記載せず、詳細は `docs/` を参照します。

ユーザーの発言の解釈方法は `docs/agent-chat-rule/` 内のドキュメントを参照してください。
