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

## Local Run

```bash
poetry install
python manage.py migrate
python manage.py runserver
```

Compose 起動時は app コンテナが `migrate --noinput` を実行してから `runserver` を立ち上げます。`.env` がない場合でも `POSTGRES_*` 系の既定値で PostgreSQL 接続設定を解決します。
