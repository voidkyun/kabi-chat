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

### 2. Backend を Compose で起動する

```bash
docker compose up --build app db
```

app コンテナが起動時に `python manage.py migrate --noinput` を実行してから `runserver` を立ち上げます。Django の管理コマンドを手動で実行したい場合は、ルートで `docker compose exec app python manage.py <command>` を利用します。

### 3. Frontend の依存関係を導入する

```bash
cd frontend
npm install
```

## Local Development Flow

- Frontend 実装は `frontend/` 配下で進めます
- Backend 実装は `backend/` 配下で進めます
- Backend とローカル DB はルート `docker-compose.yml` で管理します
- Infrastructure は `infra/terraform/` 配下で `dev` / `prod` を分離します
- 詳細な実装責務は `docs/architecture/*.md` を参照します

## Current Bootstrap Status

現在は Django / DRF の基盤と PostgreSQL 接続設定までを導入済みです。Discord OAuth2、JWT、各ドメインの永続化モデルと業務ロジックは後続 issue で追加します。
