# Backend Workspace

`backend/` は Django / DRF API を配置する領域です。

## Directory Intent

- `apps/auth/`
  - Discord OAuth2 login, JWT 発行、現在ユーザー取得
- `apps/workspaces/`
  - workspace の管理
- `apps/channels/`
  - channel の管理
- `apps/messages/`
  - message の一覧取得、投稿
- `apps/macros/`
  - macro の取得、更新

MVP の実装詳細は `docs/architecture/backend.md` と `docs/architecture/auth.md` を参照してください。
