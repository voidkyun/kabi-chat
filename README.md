# kabi-chat

markdown, tex をサポートする軽量なチャットツールです。Frontend / Backend / Infrastructure / docs をモノレポで管理します。

## Repository Layout

```text
.
├── frontend/              # React SPA (npm)
├── backend/               # Django / DRF API (Poetry)
├── infra/
│   └── terraform/         # AWS IaC (Terraform)
├── docs/                  # アーキテクチャと運用ルールの正本
├── docker-compose.yml     # ローカル開発用の共通サービス
└── .env.example           # ローカル環境変数のひな形
```

## Tool Placement

- npm: `frontend/package.json`
- Poetry: `backend/pyproject.toml`
- Terraform: `infra/terraform/`
- Docker Compose: ルート `docker-compose.yml`

## Quick Start

### 1. 環境変数を用意する

```bash
cp .env.example .env
```

Discord Developer Portal の OAuth2 redirect は `.env` の `DISCORD_REDIRECT_URI` と完全一致させてください。ローカル既定値は `http://localhost:8000/auth/discord/callback` です。認証成功後に Frontend へ戻す URL は `AUTH_FRONTEND_CALLBACK_URL` で制御し、ローカル既定値は `http://localhost:5173/login/callback` です。

### 2. Backend を Compose で起動する

```bash
docker compose up --build app db
```

app コンテナが起動時に `python manage.py migrate --noinput` を実行してから `runserver` を立ち上げます。Django の管理コマンドを手動で実行したい場合は、ルートで `docker compose exec app python manage.py <command>` を利用します。

テストはルートで `docker compose exec app pytest` を利用します。

### 3. Frontend の依存関係を導入する

```bash
cd frontend
npm install
npm run dev
```

Vite 開発サーバーは `http://localhost:5173` を既定とし、Backend API (`http://localhost:8000`) への proxy を設定しています。

## Local Development Flow

- Frontend 実装は `frontend/` 配下で進めます
- Backend 実装は `backend/` 配下で進めます
- Backend とローカル DB はルート `docker-compose.yml` で管理します
- Infrastructure は `infra/terraform/` 配下で `dev` / `prod` を分離します
- アーリーアクセスの常設クラウド環境は低コストな単一 instance 構成を前提とします
- 本番配備素材は `infra/deploy/prod/` に置き、reverse proxy + backend + PostgreSQL を同一 host に載せます
- `main` merge から prod deploy までは GitHub Actions で自動化し、詳細は `docs/dev-workflow/prod-deploy.md` を参照します
- GitHub Actions には backend 向け検証に加えて、`frontend/**` 変更時に `npm ci`、`npm run test -- --run`、`npm run build` を実行する `frontend-build` workflow があります
- 詳細な実装責務は `docs/architecture/*.md` を参照します

## Current Bootstrap Status

現在は Django / DRF 基盤に加えて、Discord OAuth2 + JWT の認証 API と MVP の domain API を導入済みです。Frontend には React SPA の初期構成が入り、認証導線、workspace の作成と選択 UI、workspace owner 向け channel 作成 UI、message 一覧、message 投稿、message ごとの raw/view 切替、Markdown + TeX 描画、effective macro 一覧を確認できます。`GET /auth/discord/login`、`GET /auth/discord/callback`、`GET /auth/me`、`POST /auth/token/refresh`、`POST /auth/logout` に加えて、`/workspaces`、`/channels`、`/messages`、`/macros` が利用できます。Discord callback は Backend で token を発行した後、`AUTH_FRONTEND_CALLBACK_URL` が設定されていれば Frontend (`/login/callback`) に戻り、React 側で access token を取り込んでログイン状態を確立します。さらに page reload や新規 tab では refresh token cookie から session を再確立し、複数 API request が同時に `401` を受けても refresh は 1 回に集約されます。macro は `global / workspace / channel` の 3 スコープを持ち、`GET /macros/?effective=true&workspace_id=...` または `channel_id=...` で `channel > workspace > global` の優先順位を解決した一覧を取得できます。`workspace_id` と `channel_id` を同時に渡す場合は、`channel` がその `workspace` 配下に属している必要があります。CI は backend 系 workflow に加えて frontend の test と build も検証します。
