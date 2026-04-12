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

## Bootstrap Status

- Django project: `config/`
- Django apps: `apps/auth/`, `apps/workspaces/`, `apps/channels/`, `apps/messages/`, `apps/macros/`
- Entrypoint: `manage.py`
- Health check: `GET /healthz/`
- Auth API: `GET /auth/discord/login`, `GET /auth/discord/callback`, `GET /auth/me`, `POST /auth/token/refresh`, `POST /auth/logout`
- Auth persistence: user profile と refresh token 永続化
- Workspace API: `GET/POST /workspaces/`, `GET/PATCH /workspaces/{id}/`
- Channel API: `GET/POST /channels/`, `GET/PATCH /channels/{id}/`
- Message API: `GET /messages/?channel_id=...`, `POST /messages/`
- Macro API: `GET/POST /macros/`, `PATCH /macros/{id}/`, `GET /macros/?effective=true&workspace_id=...`, `GET /macros/?effective=true&channel_id=...`
- Permission baseline: workspace member は参照可能、workspace owner は scoped resource を更新可能、global macro 更新は staff のみ

## Local Run

```bash
cd ..
docker compose up --build app db
```

Compose 起動時は app コンテナが `migrate --noinput` を実行してから `runserver` を立ち上げます。Django の管理コマンドを手動で実行する場合は、ルートディレクトリで `docker compose exec app python manage.py <command>` を利用してください。`.env` がない場合でも `POSTGRES_*` 系の既定値で PostgreSQL 接続設定を解決します。

ホストの Python は利用せず、Backend のコマンドは app コンテナ内で実行します。

テストはルートディレクトリで `docker compose exec app pytest` を利用します。
